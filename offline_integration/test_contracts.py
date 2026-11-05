"""C01-C20: frozen offline contracts, with forbidden-operation tripwires per test."""

import datetime as dt
import json
import socket
import subprocess
import threading
import urllib.request
from dataclasses import asdict, replace
from unittest.mock import Mock

import pytest
from boundary import OfflinePrototype
from gateway import Gateway
from http_fixture_harness import HttpFixtureHarness
from knowledge_preflight import OfflineKnowledgePreflight, RequestV1, identity
from mock_harness import MockHarness
from private_draft_lifecycle import OfflinePrivateDraftLifecycle

from moriq.knowledge.registry import Registry
from offline_integration.contracts import ActorContext, OfflineAdapter, RequestEnvelope, SourceReference

SECRET = 'PRIVATE_CANARY_6_1A'
REQUEST = RequestV1(SECRET + ' question', 'synthetic stair width', 'TESTLAND', 'TEST-v1')
REF = SourceReference('SYNTHETIC-SOURCE', '1' * 64, '2' * 64)
CREDENTIALS = {f'test-{r}': (r, r) for r in ('SA', 'IR', 'AP', 'QR', 'PV', 'RA')}


@pytest.fixture(autouse=True)
def synthetic_clock(monkeypatch):
    # Existing lifecycle requires agreeing UTC and local dates; disagreement still denies.
    class Date(dt.date):
        @classmethod
        def today(cls):
            return cls(2026, 11, 2)

    class Time(dt.datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 11, 2, 12, tzinfo=tz)

    monkeypatch.setattr(dt, 'date', Date)
    monkeypatch.setattr(dt, 'datetime', Time)


@pytest.fixture(autouse=True)
def no_external_access(monkeypatch):
    traps = []
    targets = [
        (socket, 'socket'),
        (subprocess, 'Popen'),
        (urllib.request, 'urlopen'),
        (Gateway, 'respond'),
        (OfflinePrototype, 'public'),
        (OfflinePrototype, 'view'),
        (MockHarness, 'public'),
        (HttpFixtureHarness, 'public'),
        (OfflineKnowledgePreflight, 'prepare'),
        (OfflineKnowledgePreflight, 'check'),
        (OfflinePrivateDraftLifecycle, 'prepare'),
        (OfflinePrivateDraftLifecycle, 'begin_fixture'),
        (OfflinePrivateDraftLifecycle, 'complete_fixture'),
        (OfflinePrivateDraftLifecycle, 'view_fixture'),
    ]
    targets += [(Registry, name) for name in ('snapshot', 'chunks', 'inspect', 'propose', 'approve', 'ingest')]
    for owner, name in targets:
        trap = Mock(side_effect=AssertionError('Forbidden offline operation'))
        monkeypatch.setattr(owner, name, trap)
        traps.append(trap)
    yield
    assert all(t.call_count == 0 for t in traps), 'Provider/source/private API called'


def build(refs=(REF,)):
    boundary, executor = object(), object()
    app = OfflineAdapter(
        boundary_key=boundary,
        executor_key=executor,
        credentials=CREDENTIALS,
        request_references={identity(asdict(REQUEST)): refs},
    )
    actor = app.bind(boundary, 'actor-one', 'session-one')
    req = RequestEnvelope(1, 'r1', 'session-one', REQUEST, refs)
    return app, boundary, executor, actor, req


def public(result):
    value = json.loads(result.public_json())
    assert value['sources'] == [] and value['release_allowed'] is False
    assert value['claim_status'] == 'not_assessed'
    assert SECRET not in result.public_json().decode()
    assert 'SYNTHETIC-SOURCE' not in result.public_json().decode()
    return value


def test_C01_progression():
    app, _, executor, actor, req = build()
    receipt = app.start(actor, req)
    assert public(receipt)['status'] == 'accepted'
    assert len(receipt.cancel_authority) == 64
    assert public(app.advance(executor, 'r1', 1))['status'] == 'validating'
    end = app.advance(executor, 'r1', 2)
    assert public(end)['code'] == 'generation_disabled'
    assert end.status == 'failed' and end.terminal and end.revision == 3
    assert app.status(actor, 'r1') == end


@pytest.mark.parametrize(
    'change',
    [
        {'request_id': ''},
        {'request_id': []},
        {'session': ''},
        {'request_id': 'x' * 65},
        {'request': {}},
        {'request': replace(REQUEST, max_hits=True)},
        {'request': replace(REQUEST, max_hits=17)},
        {'request': replace(REQUEST, question=' ')},
        {'request': replace(REQUEST, question='x' * 513)},
        {'request': replace(REQUEST, question='\ud800')},
        {'request': replace(REQUEST, scope='unknown')},
        {'request': replace(REQUEST, format='other')},
        {'approved_source_references': [REF]},
        {'approved_source_references': (REF,) * 17},
        {'approved_source_references': (SourceReference('bad source', '1' * 64, '2' * 64),)},
        {'approved_source_references': (SourceReference('s', 'bad', '2' * 64),)},
    ],
)
def test_C02_malformed(change):
    app, _, _, actor, req = build()
    assert public(app.start(actor, replace(req, **change)))['code'] == 'invalid_request'
    assert not app._pending and not app._owner._contexts


@pytest.mark.parametrize('payload', [None, {}, {'actor': 'admin'}, {'provider': 'ollama'}, SECRET, []])
def test_C02_untyped(payload):
    app, _, _, actor, _ = build()
    assert public(app.start(actor, payload))['code'] == 'invalid_request'
    assert not app._pending


@pytest.mark.parametrize('version', [0, 2, -1, True, '1', None])
def test_C03_version(version):
    app, _, _, actor, req = build()
    assert public(app.start(actor, replace(req, version=version)))['code'] == 'unsupported_version'


def test_C04_context_is_not_a_client_claim():
    app, _, _, actor, req = build()
    for fake in [None, asdict(actor), ActorContext(actor.actor, actor.session), replace(actor)]:
        assert public(app.start(fake, req))['code'] == 'denied'
    with pytest.raises(ValueError, match='Context unavailable'):
        app.bind(object(), actor.actor, actor.session)


def test_C05_cross_actor_and_no_existence_oracle():
    app, boundary, _, actor, req = build()
    receipt = app.start(actor, req)
    other = app.bind(boundary, 'actor-two', actor.session)
    outputs = [
        app.status(other, 'r1'),
        app.status(other, 'missing'),
        app.cancel(other, 'r1', receipt.cancel_authority),
        app.status(actor, []),
    ]
    assert len({r.public_json() for r in outputs}) == 1
    assert public(app.start(other, req))['code'] == 'denied'
    assert app.status(actor, 'r1').status == 'accepted'


def test_C06_sessions_copies_and_revocation():
    app, boundary, executor, actor, req = build()
    receipt = app.start(actor, req)
    other = app.bind(boundary, actor.actor, 'session-two')
    assert public(app.start(other, replace(req, request_id='r2')))['code'] == 'denied'
    for ctx in (other, replace(actor)):
        assert public(app.status(ctx, 'r1'))['code'] == 'denied'
        assert public(app.cancel(ctx, 'r1', receipt.cancel_authority))['code'] == 'denied'
    app.revoke(boundary, actor)
    assert public(app.status(actor, 'r1'))['code'] == 'denied'
    assert public(app.advance(executor, 'r1', 1))['code'] == 'denied'
    fresh = app.bind(boundary, actor.actor, actor.session)
    assert public(app.status(fresh, 'r1'))['code'] == 'denied'


@pytest.mark.parametrize(
    'refs,code',
    [
        ((), 'source_reference_denied'),
        ((replace(REF, document_id='3' * 64),), 'source_reference_denied'),
        ((replace(REF, source_id='another'),), 'source_reference_denied'),
        ((replace(REF, chunk_id='4' * 64),), 'source_reference_denied'),
        ((REF, REF), 'invalid_request'),
        (({'approved': True},), 'invalid_request'),
    ],
)
def test_C07_source_references(refs, code):
    app, _, _, actor, req = build()
    assert public(app.start(actor, replace(req, approved_source_references=refs)))['code'] == code
    assert not app._owner._contexts


@pytest.mark.parametrize('mode', ['live', 'ollama', 'http://127.0.0.1:11434', 'mock-success', True, None])
def test_C08_no_generation_mode(mode):
    app, _, _, actor, req = build()
    assert public(app.start(actor, replace(req, generation=mode)))['code'] == 'generation_disabled'
    assert not app._owner._contexts
    assert not hasattr(app, 'provider')


@pytest.mark.parametrize('end', ['active', 'cancelled', 'failed'])
def test_C09_duplicate_replay(end):
    app, _, executor, actor, req = build()
    receipt = app.start(actor, req)
    if end == 'cancelled':
        app.cancel(actor, 'r1', receipt.cancel_authority)
    if end == 'failed':
        app.advance(executor, 'r1', 1)
        app.advance(executor, 'r1', 2)
    old = app.status(actor, 'r1')
    for _ in range(2):
        assert public(app.start(actor, req))['code'] == 'duplicate_request'
    assert len(app._owner._contexts) == 1 and app.status(actor, 'r1') == old


def test_C10_request_scoped_cancel_and_repeat():
    app, _, _, actor, req = build()
    a = app.start(actor, req)
    b = app.start(actor, replace(req, request_id='r2'))
    for key in (None, '', [], b.cancel_authority):
        assert public(app.cancel(actor, 'r1', key))['code'] == 'denied'
    end = app.cancel(actor, 'r1', a.cancel_authority)
    assert public(end)['status'] == 'cancelled' and end.terminal
    assert app.cancel(actor, 'r1', a.cancel_authority) == end
    assert app.status(actor, 'r2').status == 'accepted'


@pytest.mark.parametrize('terminal', ['cancelled', 'failed'])
def test_C11_stale_and_terminal(terminal):
    app, _, executor, actor, req = build()
    receipt = app.start(actor, req)
    assert public(app.advance(executor, 'r1', True))['code'] == 'stale_response'
    app.advance(executor, 'r1', 1)
    assert public(app.advance(executor, 'r1', 1))['code'] == 'stale_response'
    if terminal == 'cancelled':
        end = app.cancel(actor, 'r1', receipt.cancel_authority)
    else:
        end = app.advance(executor, 'r1', 2)
        assert public(app.cancel(actor, 'r1', receipt.cancel_authority))['code'] == 'terminal_state'
    assert public(app.advance(executor, 'r1', 2))['code'] == 'stale_response'
    assert public(app.advance(executor, 'r1', end.revision))['code'] == 'terminal_state'
    assert app.status(actor, 'r1') == end


def test_C12_executor_authority():
    app, boundary, _, actor, req = build()
    receipt = app.start(actor, req)
    for key in (object(), actor, boundary, receipt.cancel_authority):
        assert public(app.advance(key, 'r1', 1))['code'] == 'denied'
    assert app.status(actor, 'r1').status == 'accepted'


@pytest.mark.parametrize('winner', ['cancel', 'complete'])
def test_C13_ordered_race(winner):
    app, _, executor, actor, req = build()
    receipt = app.start(actor, req)
    app.advance(executor, 'r1', 1)
    first_done = threading.Event()
    outputs = []

    def perform(which):
        if which != winner:
            assert first_done.wait(2)
        result = (
            app.cancel(actor, 'r1', receipt.cancel_authority) if which == 'cancel' else app.advance(executor, 'r1', 2)
        )
        outputs.append(result)
        if which == winner:
            first_done.set()

    threads = [threading.Thread(target=perform, args=(which,)) for which in ('cancel', 'complete')]
    for t in threads:
        t.start()
    for t in threads:
        t.join(3)
        assert not t.is_alive()
    assert len(outputs) == 2
    end = app.status(actor, 'r1')
    assert public(end)['status'] == ('cancelled' if winner == 'cancel' else 'failed')
    assert end.terminal and end.revision == 3


def test_C13_simultaneous_race():
    app, _, executor, actor, req = build()
    receipt = app.start(actor, req)
    app.advance(executor, 'r1', 1)
    barrier = threading.Barrier(3)
    results = []

    def worker(cancel):
        barrier.wait(2)
        results.append(app.cancel(actor, 'r1', receipt.cancel_authority) if cancel else app.advance(executor, 'r1', 2))

    threads = [threading.Thread(target=worker, args=(flag,)) for flag in (True, False)]
    for t in threads:
        t.start()
    barrier.wait(2)
    for t in threads:
        t.join(3)
        assert not t.is_alive()
    assert len(results) == 2 and sum(r.terminal for r in results) == 1
    assert public(app.status(actor, 'r1'))['revision'] == 3


def test_C14_concurrent_start():
    app, _, _, actor, req = build()
    barrier = threading.Barrier(3)
    results = []

    def worker():
        barrier.wait(2)
        results.append(app.start(actor, req))

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for t in threads:
        t.start()
    barrier.wait(2)
    for t in threads:
        t.join(3)
        assert not t.is_alive()
    assert sorted(public(r)['status'] for r in results) == ['accepted', 'error']
    assert len(app._owner._contexts) == 1


def test_C15_sanitized_failure(monkeypatch):
    app, _, _, actor, req = build()
    results = []
    for text in (SECRET, 'different confidential detail'):
        monkeypatch.setattr(app._owner, 'create_request', Mock(side_effect=RuntimeError(text)))
        results.append(app.start(actor, req).public_json())
    assert results[0] == results[1]
    assert json.loads(results[0])['code'] == 'unavailable'
    assert SECRET.encode() not in results[0] and not app._pending


def test_C16_source_gap():
    app, _, executor, actor, req = build(refs=())
    app.start(actor, req)
    app.advance(executor, 'r1', 1)
    result = public(app.advance(executor, 'r1', 2))
    assert result['status'] == 'failed' and result['code'] == 'source_gap' and result['sources'] == []


def test_C17_existing_authority_and_pins():
    app, _, _, actor, req = build()
    assert type(app._owner) is OfflinePrivateDraftLifecycle
    assert (
        public(app.start(actor, replace(req, request=replace(REQUEST, question='another question'))))['code']
        == 'denied'
    )
    app._owner._authority.available = False
    assert public(app.start(actor, req))['code'] == 'unavailable'
    assert not app._pending


def test_C18_public_projection():
    app, _, executor, actor, req = build()
    receipt = app.start(actor, req)
    for result in (receipt, app.status(actor, 'r1'), app.advance(executor, 'r1', 1), app.advance(executor, 'r1', 2)):
        value = public(result)
        assert set(value) == {
            'version',
            'status',
            'code',
            'request_id',
            'revision',
            'terminal',
            'claim_status',
            'release_allowed',
            'sources',
        }
        for forbidden in (actor.actor, actor.session, receipt.cancel_authority, SECRET, 'draft', REF.document_id):
            assert forbidden not in result.public_json().decode()
    assert SECRET not in repr(req) and receipt.cancel_authority not in repr(receipt)


def test_C19_capacity():
    app, boundary, _, actor, req = build()
    for i in range(15):
        app.bind(boundary, 'actor', f'session-{i}')
    with pytest.raises(ValueError, match='Context unavailable'):
        app.bind(boundary, 'actor', 'overflow')
    for i in range(32):
        receipt = app.start(actor, replace(req, request_id=f'r{i}'))
        assert public(receipt)['status'] == 'accepted'
        app.cancel(actor, f'r{i}', receipt.cancel_authority)
    assert public(app.start(actor, replace(req, request_id='overflow')))['code'] == 'resource_limit'
    assert len(app._pending) == 32


def test_C20_new_owner():
    app, _, _, actor, req = build()
    old = app.start(actor, req)
    fresh, _, _, new_actor, _ = build()
    assert public(fresh.start(actor, req))['code'] == 'denied'
    fresh.start(new_actor, req)
    assert public(fresh.cancel(new_actor, 'r1', old.cancel_authority))['code'] == 'denied'


def test_C07_cross_request_pin():
    boundary, executor = object(), object()
    second = replace(REQUEST, question='another synthetic question')
    other = replace(REF, source_id='OTHER-SYNTHETIC')
    app = OfflineAdapter(
        boundary_key=boundary,
        executor_key=executor,
        credentials=CREDENTIALS,
        request_references={identity(asdict(REQUEST)): (REF,), identity(asdict(second)): (other,)},
    )
    actor = app.bind(boundary, 'actor', 'session')
    bad = RequestEnvelope(1, 'r', 'session', second, (REF,))
    assert public(app.start(actor, bad))['code'] == 'source_reference_denied'
    assert public(app.start(actor, replace(bad, approved_source_references=(other,))))['status'] == 'accepted'


def test_C17_clock_disagreement(monkeypatch):
    app, _, _, actor, req = build()

    class WrongDate(dt.date):
        @classmethod
        def today(cls):
            return cls(2026, 11, 1)

    monkeypatch.setattr(dt, 'date', WrongDate)
    assert public(app.start(actor, req))['code'] == 'unavailable'
    assert not app._pending and app._owner._healthy is False


def test_C17_audit_failure(monkeypatch):
    app, _, _, actor, req = build()
    monkeypatch.setattr(app._owner, '_audit', Mock(side_effect=RuntimeError(SECRET)))
    assert public(app.start(actor, req))['code'] == 'unavailable'
    assert not app._pending and app._owner._healthy is False


def test_C02_encoded_size_limit():
    app, _, _, actor, req = build()
    large = replace(
        REQUEST,
        question='\U0001f600' * 512,
        search_query='\U0001f600' * 512,
        jurisdiction='\U0001f600' * 256,
        edition='\U0001f600' * 256,
    )
    assert public(app.start(actor, replace(req, request=large)))['code'] == 'invalid_request'


def test_C04_invalid_configuration():
    key = object()
    with pytest.raises(ValueError, match='Distinct host capabilities'):
        OfflineAdapter(boundary_key=key, executor_key=key, credentials=CREDENTIALS, request_references={})
    with pytest.raises(ValueError, match='Invalid offline configuration'):
        OfflineAdapter(
            boundary_key=key, executor_key=object(), credentials=CREDENTIALS, request_references={'not-a-hash': ()}
        )
