"""Offline connectivity tests. Only literal synthetic source setup can ingest."""

import datetime as dt
import json
import socket
import subprocess
import threading
import urllib.request
from dataclasses import asdict
from unittest.mock import Mock

import pytest
from boundary import OfflinePrototype
from gateway import Gateway
from knowledge_preflight import RequestV1, identity
from private_draft_lifecycle import OfflinePrivateDraftLifecycle

from moriq.knowledge.registry import Registry, SourceMetadata, sha256
from offline_integration.backend import OfflineBackend
from offline_integration.contracts import SourceReference
from offline_integration.test_contracts import CREDENTIALS, synthetic_clock  # noqa: F401

BODY = b'SYNTHETIC TEST ONLY: thermal bridge example; not architectural guidance.'
REQ = RequestV1('Explain synthetic thermal bridge', 'thermal bridge', 'TESTLAND', 'TEST-v1')
SECRET = 'PRIVATE_BACKEND_CANARY'


@pytest.fixture(autouse=True)
def no_provider(monkeypatch):
    targets = [(socket, 'socket'), (subprocess, 'Popen'), (urllib.request, 'urlopen'),
               (Gateway, 'respond'), (OfflinePrototype, 'public'), (OfflinePrototype, 'view')]
    targets += [(OfflinePrivateDraftLifecycle, name) for name in
                ('prepare', 'begin_fixture', 'complete_fixture', 'request_view', 'view_fixture')]
    traps = []
    for owner, name in targets:
        trap = Mock(side_effect=AssertionError('Forbidden operation'))
        monkeypatch.setattr(owner, name, trap)
        traps.append(trap)
    yield
    assert all(t.call_count == 0 for t in traps)


@pytest.fixture
def system(monkeypatch, request):
    registry = Registry({'author': ('author', {'author'}), 'reviewer': ('reviewer', {'reviewer'})})
    meta = SourceMetadata('SYNTHETIC', 'Synthetic note', 'https://example.org/test', 'code', 'text',
                          'CC0-1.0', 'public_redistribution', 'public', sha256(BODY), 'test-v1',
                          jurisdiction='TESTLAND', code_edition='TEST-v1')
    record = registry.propose('author', meta)
    registry.approve('reviewer', 'SYNTHETIC', record.document_id)
    chunks = registry.ingest('author', 'SYNTHETIC', BODY)
    ref = SourceReference(chunks[0].source_id, chunks[0].document_id, chunks[0].chunk_id)
    state = getattr(request, 'param', 'active')
    if state == 'pending':
        registry.propose('author', meta)
    if state == 'revoked':
        registry.withdraw('reviewer', 'SYNTHETIC', state='revoked')
    refs = () if state == 'empty' else (ref,)
    key = object()
    backend = OfflineBackend(server_key=key, credentials=CREDENTIALS,
                             request_references={identity(asdict(REQ)): refs}, registry=registry)
    ticket = backend.issue_session(key, 'user-a', 'session-a')
    payload = {'version': 1, 'op': 'start', 'request_id': 'r1', 'request': asdict(REQ),
               'sources': [asdict(r) for r in refs]}
    traps = []
    for name in ('ingest', 'propose', 'approve'):
        trap = Mock(side_effect=AssertionError('No ingestion/approval through backend'))
        monkeypatch.setattr(Registry, name, trap)
        traps.append(trap)
    yield backend, key, ticket, registry, payload
    assert all(t.call_count == 0 for t in traps)


def call(backend, ticket, payload):
    raw = payload if type(payload) is bytes else json.dumps(payload).encode()
    return check(backend.handle(ticket, raw))


def check(raw):
    value = json.loads(raw)
    assert value['sources'] == [] and value['claim_status'] == 'not_assessed'
    assert value['release_allowed'] is False
    assert SECRET.encode() not in raw and BODY not in raw
    assert set(value) == {'version', 'status', 'code', 'request_id', 'revision', 'terminal',
                          'claim_status', 'release_allowed', 'sources'}
    return value


def command(op, rid='r1'):
    return {'version': 1, 'op': op, 'request_id': rid}


def test_B01_connectivity(system):
    backend, key, ticket, _, payload = system
    assert call(backend, ticket, payload)['status'] == 'accepted'
    assert call(backend, ticket, command('status'))['revision'] == 1
    assert check(backend.tick(key, ticket, 'r1', 1))['status'] == 'validating'
    result = check(backend.tick(key, ticket, 'r1', 2))
    assert result['status'] == 'failed' and result['code'] == 'generation_disabled' and result['terminal']


@pytest.mark.parametrize('payload', [b'', b'{', b'[]', b'null', b'\xff', pytest.param(b'x' * 32769, id='oversized'),
                                    b'{"version":1,"version":1}', b'{"version":NaN}',
                                    b'{"version":Infinity}', b'[' * 2000])
def test_B02_malformed(system, payload):
    backend, _, ticket, _, _ = system
    assert call(backend, ticket, payload)['code'] == 'invalid_request'
    assert not backend._jobs


@pytest.mark.parametrize('version', [0, 2, True, '1', None])
def test_B03_versions(system, version):
    backend, _, ticket, _, payload = system
    assert call(backend, ticket, dict(payload, version=version))['code'] == 'unsupported_version'


@pytest.mark.parametrize('field', ['actor', 'session', 'token', 'reviewer', 'approved', 'endpoint', 'model'])
def test_B04_client_authority(system, field):
    backend, _, ticket, _, payload = system
    assert call(backend, ticket, dict(payload, **{field: SECRET}))['code'] == 'invalid_request'
    for fake in [None, object(), {'actor': 'user-a'}, 'user-a']:
        assert call(backend, fake, payload)['code'] == 'denied'


@pytest.mark.parametrize('actor,session', [('user-b', 'session-a'), ('user-a', 'session-b')])
def test_B05_cross_identity(system, actor, session):
    backend, key, ticket, _, payload = system
    other = backend.issue_session(key, actor, session)
    call(backend, ticket, payload)
    for op in ['status', 'cancel']:
        assert call(backend, other, command(op))['code'] == 'denied'
    assert call(backend, other, payload)['code'] == 'denied'
    assert check(backend.tick(key, other, 'r1', 1))['code'] == 'denied'


@pytest.mark.parametrize('terminal', ['active', 'cancelled', 'failed'])
def test_B06_replay(system, terminal):
    backend, key, ticket, _, payload = system
    call(backend, ticket, payload)
    if terminal == 'cancelled':
        call(backend, ticket, command('cancel'))
    if terminal == 'failed':
        backend.tick(key, ticket, 'r1', 1)
        backend.tick(key, ticket, 'r1', 2)
    before = call(backend, ticket, command('status'))
    assert call(backend, ticket, payload)['code'] == 'duplicate_request'
    assert call(backend, ticket, command('status')) == before
    assert len(backend._jobs) == 1


@pytest.mark.parametrize('op', ['advance', 'complete', 'generate', 'view', 'review', 'audit', 'approve', 'ingest'])
def test_B07_unsupported_operations(system, op):
    backend, _, ticket, _, _ = system
    assert call(backend, ticket, command(op))['code'] == 'invalid_request'


@pytest.mark.parametrize('during', [False, True])
def test_B08_cancellation(system, during):
    backend, key, ticket, _, payload = system
    call(backend, ticket, payload)
    if during:
        backend.tick(key, ticket, 'r1', 1)
    end = call(backend, ticket, command('cancel'))
    assert end['status'] == 'cancelled' and end['terminal']
    assert call(backend, ticket, command('cancel')) == end
    assert check(backend.tick(key, ticket, 'r1', end['revision']-1))['code'] == 'stale_response'
    assert check(backend.tick(key, ticket, 'r1', end['revision']))['code'] == 'terminal_state'
    assert call(backend, ticket, command('status')) == end


@pytest.mark.parametrize('first', ['cancel', 'complete'])
def test_B09_ordered_race(system, first):
    backend, key, ticket, _, payload = system
    call(backend, ticket, payload)
    backend.tick(key, ticket, 'r1', 1)
    done = threading.Event()
    outputs = []
    def run(op):
        if op != first:
            assert done.wait(3)
        outputs.append(call(backend, ticket, command('cancel')) if op == 'cancel'
                       else check(backend.tick(key, ticket, 'r1', 2)))
        if op == first:
            done.set()
    threads = [threading.Thread(target=run, args=(op,)) for op in ('cancel', 'complete')]
    for t in threads:
        t.start()
    for t in threads:
        t.join(4)
        assert not t.is_alive()
    assert len(outputs) == 2
    end = call(backend, ticket, command('status'))
    assert end['status'] == ('cancelled' if first == 'cancel' else 'failed')
    assert end['revision'] == 3


def test_B10_concurrent_isolation(system):
    backend, key, ticket, _, payload = system
    other = backend.issue_session(key, 'user-b', 'session-b')
    barrier = threading.Barrier(3)
    results = []
    def run(t, rid):
        barrier.wait(3)
        results.append(call(backend, t, dict(payload, request_id=rid)))
    threads = [threading.Thread(target=run, args=args) for args in ((ticket, 'r1'), (other, 'r2'))]
    for t in threads:
        t.start()
    barrier.wait(3)
    for t in threads:
        t.join(4)
        assert not t.is_alive()
    assert len(results) == 2 and all(r['status']=='accepted' for r in results)
    call(backend, ticket, command('cancel'))
    assert call(backend, other, command('status', 'r2'))['status'] == 'accepted'
    assert call(backend, ticket, command('status', 'r2'))['code'] == 'denied'


@pytest.mark.parametrize('cause', ['authority', 'audit'])
def test_B11_registration_failure(system, cause):
    backend, _, ticket, _, payload = system
    owner = backend._adapter._owner
    if cause == 'authority':
        owner._authority.available = False
    else:
        owner._audit_available = False
    assert call(backend, ticket, payload)['code'] == 'unavailable'
    assert not backend._jobs


@pytest.mark.parametrize('delta', [-1, 1])
def test_B12_clock_disagreement(system, monkeypatch, delta):
    backend, _, ticket, _, payload = system
    class Date(dt.date):
        @classmethod
        def today(cls):
            return cls(2026, 11, 2+delta)
    monkeypatch.setattr(dt, 'date', Date)
    assert call(backend, ticket, payload)['code'] == 'unavailable'
    assert backend._adapter._owner._healthy is False
    assert not backend._jobs


def test_B13_sanitization(system, monkeypatch):
    backend, _, ticket, registry, payload = system
    responses = []
    for msg in [SECRET, 'other private audit detail']:
        monkeypatch.setattr(registry, 'snapshot', Mock(side_effect=RuntimeError(msg)))
        responses.append(backend.handle(ticket, json.dumps(payload).encode()))
    assert responses[0] == responses[1]
    assert check(responses[0])['code'] == 'unavailable'


@pytest.mark.parametrize('system', ['pending', 'revoked'], indirect=True)
def test_B14_unapproved_sources(system):
    backend, _, ticket, _, payload = system
    assert call(backend, ticket, payload)['code'] == 'source_reference_denied'
    assert not backend._jobs


@pytest.mark.parametrize('phase', ['accepted', 'validating', 'terminal'])
def test_B15_revocation(system, phase):
    backend, key, ticket, registry, payload = system
    call(backend, ticket, payload)
    if phase != 'accepted':
        backend.tick(key, ticket, 'r1', 1)
    if phase == 'terminal':
        backend.tick(key, ticket, 'r1', 2)
    before = call(backend, ticket, command('status'))
    registry.withdraw('reviewer', 'SYNTHETIC', state='revoked')
    result = check(backend.tick(key, ticket, 'r1', before['revision']))
    assert result['code'] == ('terminal_state' if phase == 'terminal' else 'source_reference_denied')
    assert call(backend, ticket, command('status')) == before
    if phase != 'terminal':
        assert call(backend, ticket, command('cancel'))['status'] == 'cancelled'


@pytest.mark.parametrize('system', ['empty'], indirect=True)
def test_B16_source_gap(system):
    backend, key, ticket, _, payload = system
    call(backend, ticket, payload)
    backend.tick(key, ticket, 'r1', 1)
    assert check(backend.tick(key, ticket, 'r1', 2))['code'] == 'source_gap'


def test_B17_host_capabilities(system):
    backend, key, ticket, _, payload = system
    with pytest.raises(ValueError):
        backend.issue_session(object(), 'admin', 'session')
    call(backend, ticket, payload)
    assert check(backend.tick(object(), ticket, 'r1', 1))['code'] == 'denied'
    backend.revoke_session(key, ticket)
    assert call(backend, ticket, command('status'))['code'] == 'denied'
    assert check(backend.tick(key, ticket, 'r1', 1))['code'] == 'denied'


def test_B18_unpinned_no_read(system, monkeypatch):
    backend, _, ticket, registry, payload = system
    trap = Mock(side_effect=AssertionError('No read for unpinned request'))
    monkeypatch.setattr(registry, 'snapshot', trap)
    payload['request']['question'] = 'unpinned'
    assert call(backend, ticket, payload)['code'] == 'denied'
    assert trap.call_count == 0


@pytest.mark.parametrize('mode', ['live', 'ollama', 'mock-success'])
def test_B19_disabled(system, mode):
    backend, _, ticket, _, payload = system
    assert call(backend, ticket, dict(payload, generation=mode))['code'] == 'generation_disabled'
    assert not backend._jobs
