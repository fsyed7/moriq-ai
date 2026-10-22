"""4.5F supplemental authority checks; run separately from frozen registry SP cases.

Educational fixtures are denied by code-only preflight, never relabeled as code.
A distinct fictional code control tests applicability. No draft execution/viewing.
"""

import datetime as dt
import socket
import subprocess
import urllib.request
from dataclasses import asdict, replace
from unittest.mock import Mock

import knowledge_preflight as kp
import private_draft_lifecycle as life
import pytest
from boundary import OfflinePrototype
from gateway import Gateway
from test_registry_pilot import NOTES, digest, meta

from moriq.knowledge.registry import SourceMetadata

CREDS = {f'TEST_ONLY-{role}': (f'TEST_ONLY actor {role}', role) for role in ('SA', 'IR', 'AP', 'QR', 'RA', 'PV')}
CONTROL = (
    b'TEST_ONLY FICTIONAL CODE EXERCISE: imaginary stair width token cobalt. '
    b'Not an actual code or construction requirement.'
)
REAL_DATE, REAL_TIME = dt.date, dt.datetime


class Date(REAL_DATE):
    @classmethod
    def today(cls):
        return cls(2026, 10, 20)


class Time(REAL_TIME):
    @classmethod
    def now(cls, tz=None):
        return cls(2026, 10, 20, 12, tzinfo=tz)


@pytest.fixture(autouse=True)
def isolation(monkeypatch):
    monkeypatch.setattr(dt, 'date', Date)
    monkeypatch.setattr(dt, 'datetime', Time)
    traps = []
    for owner, name in (
        (socket, 'socket'),
        (subprocess, 'Popen'),
        (urllib.request, 'urlopen'),
        (OfflinePrototype, 'public'),
        (OfflinePrototype, 'view'),
        (Gateway, 'respond'),
        (kp, 'disabled_generation'),
        (life.OfflinePrivateDraftLifecycle, 'begin_fixture'),
        (life.OfflinePrivateDraftLifecycle, 'complete_fixture'),
        (life.OfflinePrivateDraftLifecycle, 'request_view'),
        (life.OfflinePrivateDraftLifecycle, 'view_fixture'),
    ):
        trap = Mock(side_effect=AssertionError('Forbidden execution/view/network'))
        monkeypatch.setattr(owner, name, trap)
        traps.append(trap)
    yield
    for trap in traps:
        trap.assert_not_called()


def request(**changes):
    return replace(
        kp.RequestV1('What code token describes this fictional stair width?', 'stair width', 'Fictionland', 'TEST-v1'),
        **changes,
    )


def control_meta():
    return SourceMetadata(
        'test45f-code-control',
        'TEST_ONLY imaginary code control',
        'https://fixtures.invalid/code-control',
        'code',
        'text',
        'TEST_ONLY dummy fixture rights; no real source authority',
        'public_redistribution',
        'public',
        digest(CONTROL),
        'v1',
        publisher='TEST_ONLY fictional publisher',
        author='TEST_ONLY SA',
        jurisdiction='Fictionland',
        code_edition='TEST-v1',
    )


def build(*, lifecycle=False, variants=()):
    req = request()
    metadata = control_meta()
    options = dict(
        request_hashes=[kp.identity(asdict(r)) for r in (req, *variants)],
        source_hashes={metadata.source_id: metadata.content_sha256},
    )
    if lifecycle:
        app = life.OfflinePrivateDraftLifecycle(CREDS, fixtures={}, **options)
    else:
        app = kp.OfflineKnowledgePreflight(
            {t: p for t, p in CREDS.items() if p[1] in {'SA', 'IR', 'AP', 'QR'}}, **options
        )
    p = app.propose_source('TEST_ONLY-SA', metadata)
    assert p.metadata == metadata
    assert app.approve_source('TEST_ONLY-IR', metadata.source_id, p.document_id) is None
    assert app.ingest('TEST_ONLY-SA', metadata.source_id, CONTROL) is None
    return app, req


def approve(app, req):
    bundle = app.prepare(req)
    assert type(bundle) is kp.BundleV1
    key = app.propose_applicability(
        'TEST_ONLY-AP', req, bundle, '1', 'TEST_ONLY exact-question dummy review; no claim approval', Date(2026, 10, 21)
    )
    assert type(key) is str
    assert app.check(req, [key]).status == 'evidence_gap'
    assert app.approve_applicability('TEST_ONLY-QR', req, bundle, key) is None
    return key


def test_F04_exact_question_and_attestation_revocation():
    changed = request(question='What code token describes a different fictional stair width?')
    app, req = build(variants=(changed,))
    assert app.check(req, []).reason == 'missing_applicability'
    key = approve(app, req)
    ready = app.check(req, [key])
    assert asdict(ready) == dict(
        status='evidence_ready', reason='structural_only', claim_status='not_assessed', release_allowed=False
    )
    assert app.check(changed, [key]).status == 'evidence_gap'
    assert app.revoke('TEST_ONLY-QR', key) is None
    assert app.check(req, [key]).reason == 'stale_attestation'


@pytest.mark.parametrize('state', ['revoked', 'retired', 'superseded'])
def test_F05_source_lifecycle(state):
    app, req = build()
    key = approve(app, req)
    assert app.withdraw_source('TEST_ONLY-IR', 'test45f-code-control', state) is None
    assert app.check(req, [key]).status == 'evidence_gap'
    assert app.prepare(req).status == 'evidence_gap'


@pytest.mark.parametrize('changes', [dict(jurisdiction='Elsewhere'), dict(edition='TEST-v2')])
def test_F06_exact_scope(changes):
    changed = request(**changes)
    app, req = build(variants=(changed,))
    key = approve(app, req)
    assert app.check(changed, [key]).status == 'evidence_gap'


def test_F07_identity_bytes_and_roles():
    app, req = build()
    metadata = control_meta()
    assert app.propose_source('TEST_ONLY-SA', replace(metadata, source_id='forged')).reason == 'authorization_missing'
    assert app.ingest('TEST_ONLY-SA', metadata.source_id, CONTROL + b'\n').status == 'evidence_gap'
    with pytest.raises(PermissionError):
        app.approve_source('TEST_ONLY-SA', metadata.source_id, '0' * 64)
    bundle = app.prepare(req)
    tampered = replace(bundle, entries=(replace(bundle.entries[0], chunk_id='0' * 64),))
    assert (
        app.propose_applicability('TEST_ONLY-AP', req, tampered, '1', 'test', Date(2026, 10, 21)).reason
        == 'binding_mismatch'
    )


@pytest.mark.parametrize('topic', list(NOTES))
def test_F08_educational_not_promoted(topic):
    body = NOTES[topic]
    metadata = meta(f'test45f-{topic}', body, reference=f'https://fixtures.invalid/{topic}', format='markdown')
    req = request(scope='general', search_query='imaginary')
    app = kp.OfflineKnowledgePreflight(
        {t: p for t, p in CREDS.items() if p[1] in {'SA', 'IR', 'AP', 'QR'}},
        request_hashes=[kp.identity(asdict(req))],
        source_hashes={metadata.source_id: digest(body)},
    )
    p = app.propose_source('TEST_ONLY-SA', metadata)
    assert app.approve_source('TEST_ONLY-IR', metadata.source_id, p.document_id) is None
    assert app.ingest('TEST_ONLY-SA', metadata.source_id, body) is None
    assert app.prepare(req).reason == 'unsupported_scope'
    assert metadata.source_type == 'educational'


def test_F09_request_context_invalidation():
    changed = request(question='What code token describes another fictional stair width?')
    app, req = build(lifecycle=True, variants=(changed,))
    context = app.create_request('TEST_ONLY-RA', req)
    assert type(context) is str
    bundle = app.prepare('TEST_ONLY-QR', context)
    key = app.propose_applicability('TEST_ONLY-AP', context, bundle, '1', 'TEST_ONLY applicability', Date(2026, 10, 21))
    assert app.approve_applicability('TEST_ONLY-QR', context, bundle, key) is None
    assert app.update_request('TEST_ONLY-SA', context, changed) == life.DENIED
    assert app.update_request('TEST_ONLY-RA', context, changed) == context
    assert app.prepare('TEST_ONLY-QR', context).request == changed
    assert app.approve_applicability('TEST_ONLY-QR', context, bundle, key) == life.DENIED
    assert (
        app.propose_applicability('TEST_ONLY-AP', context, bundle, '1', 'stale bundle', Date(2026, 10, 21))
        == life.DENIED
    )
    assert app.public_result() == life.WITHHELD
    assert app.withdraw_source('TEST_ONLY-IR', 'test45f-code-control') is None
    assert app.prepare('TEST_ONLY-QR', context) == life.DENIED


def test_F10_no_implicit_mode_or_restart_authority():
    app, req = build(lifecycle=True)
    context = app.create_request('TEST_ONLY-RA', req)
    fresh, _ = build(lifecycle=True)
    assert fresh.prepare('TEST_ONLY-QR', context) == life.DENIED
    assert fresh.create_request('TEST_ONLY-RA', request(question='MORIQ real company policy')) == life.DENIED
    assert fresh.public_result() == life.WITHHELD
