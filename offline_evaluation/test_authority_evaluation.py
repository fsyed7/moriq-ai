"""Synthetic fixture-copy authority evaluation. No generated draft or endpoint."""

import ast
import datetime as dt
import inspect
import json
import sys
import threading
from dataclasses import asdict, replace
from pathlib import Path
from unittest.mock import Mock

import knowledge_preflight as kp
import private_draft_lifecycle as life
import pytest
import test_authority_pilot as f
import test_knowledge_preflight as k
import test_private_draft_lifecycle as b
from boundary import OfflinePrototype
from gateway import Gateway

from offline_evaluation.conftest import no_leak
from offline_evaluation.fixtures import SPEC, Date, Time

H = SPEC['global_contracts_v2']['held_fixture']['text']
D = life.DENIED
CASES = [c for c in SPEC['cases'] if c['case_id'] in {'E11', 'E12', 'E13', 'E14', 'E15', 'E21'}]


@pytest.fixture(autouse=True)
def isolated(monkeypatch):
    Time.current = (2026, 10, 16, 12, 0, 0)
    monkeypatch.setattr(dt, 'date', Date)
    monkeypatch.setattr(dt, 'datetime', Time)
    monkeypatch.setattr(b, 'Date', Date)
    monkeypatch.setattr(b, 'Time', Time)
    monkeypatch.setattr(k, 'FixedDate', Date)
    monkeypatch.setattr(f, 'Date', Date)
    traps = []
    for owner, name in (
        (OfflinePrototype, 'public'),
        (OfflinePrototype, 'view'),
        (Gateway, 'respond'),
        (kp, 'disabled_generation'),
    ):
        trap = Mock(side_effect=AssertionError('Forbidden generator or Task3 viewer'))
        monkeypatch.setattr(owner, name, trap)
        traps.append(trap)
    original_view = life.OfflinePrivateDraftLifecycle.view_fixture

    def checked_view(owner, *args):
        result = original_view(owner, *args)
        if result == D:
            no_leak(result)
        else:
            value = json.loads(result)
            assert set(value) == {
                'status',
                'synthetic',
                'claim_status',
                'release_allowed',
                'text',
                'aliases',
                'draft_id',
            }
            assert value['text'] == H and value['synthetic'] is True and (value['release_allowed'] is False)
        no_leak(json.dumps([asdict(e) for e in owner._events]))
        return result

    monkeypatch.setattr(life.OfflinePrivateDraftLifecycle, 'view_fixture', checked_view)
    yield
    assert all(t.call_count == 0 for t in traps)


class Observe:
    """Delegates unchanged require decisions; stores symbols, never private values."""

    def __init__(self, monkeypatch):
        self.events = []
        self.unexpected = []
        mapping = {}
        tree = ast.parse(Path(life.__file__).read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                calls = sorted(
                    (
                        n
                        for n in ast.walk(node)
                        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and (n.func.id == 'require')
                    ),
                    key=lambda n: n.lineno,
                )
                for index, call in enumerate(calls):
                    mapping[node.name, call.lineno] = node.name + ':guard' + str(index)
        original = life.require

        def require(value):
            frame = inspect.currentframe().f_back
            symbol = mapping[frame.f_code.co_name, frame.f_lineno]
            self.events.append((symbol, bool(value)))
            return original(value)

        monkeypatch.setattr(life, 'require', require)
        original_audit = life.OfflinePrivateDraftLifecycle._audit

        def audit(owner, *args):
            try:
                return original_audit(owner, *args)
            except life.Denial:
                self.events.append(('audit_capacity_or_availability', False))
                raise

        monkeypatch.setattr(life.OfflinePrivateDraftLifecycle, '_audit', audit)
        paths = {life.__file__, kp.__file__}
        self.old = sys.gettrace()
        self.old_thread = threading.gettrace()

        def trace(frame, event, arg):
            if event == 'exception' and frame.f_code.co_filename in paths:
                cls = arg[0]
                if cls not in (life.Denial, kp.Denied, StopIteration, GeneratorExit):
                    self.unexpected.append(cls.__name__)
            return trace

        sys.settrace(trace)
        threading.settrace(trace)

    def close(self):
        sys.settrace(self.old)
        threading.settrace(self.old_thread)
        assert not self.unexpected, 'Unexpected runtime exception category'

    def failed(self, function, index=None):
        failed = [x for x, ok in self.events if not ok]
        expected = function if index is None else function + ':guard' + str(index)
        assert failed and (failed[0] == expected if index is not None else failed[0].split(':')[0] == function), failed


def held(app, c, ids, grant=True):
    d = app.begin_fixture('f', c, ids)
    assert type(d) is str
    assert app.complete_fixture(d) == d
    if grant:
        assert app.grant_reviewer(d, Time.now(dt.UTC) + dt.timedelta(seconds=120)) is None
    return d


def build(variants=()):
    return b.build(text=H, variants=variants)


def copy(app, p, d):
    payload = app.view_fixture('fixture-pv', p)
    assert json.loads(payload) == dict(
        status='private_draft',
        synthetic=True,
        claim_status='not_assessed',
        release_allowed=False,
        text=H,
        aliases=['1'],
        draft_id=d,
    )
    assert app.public_result() == life.WITHHELD
    return payload


def positive(monkeypatch):
    app, c, ids = build()
    d = held(app, c, ids)
    first = copy(app, b.permit(app, d), d)
    with monkeypatch.context() as mp:
        observer = Observe(mp)
        try:
            second = copy(app, b.permit(app, d), d)
            assert second == first and (not [x for x, ok in observer.events if not ok])
        finally:
            observer.close()


def decision(value, status, reason):
    assert asdict(value) == dict(status=status, reason=reason, claim_status='not_assessed', release_allowed=False)


@pytest.mark.parametrize(
    'case,variant',
    [(c['case_id'], v) for c in CASES for v in c['variants']],
    ids=[c['case_id'] + '/' + v for c in CASES for v in c['variants']],
)
def test_frozen(case, variant, monkeypatch, record_property):
    record_property('case_id', case)
    record_property('variant_id', variant)
    if case in ('E11', 'E12'):
        evaluate_preflight(case, variant)
        count = (
            1
            if case == 'E12' or variant == 'missing_question_approval'
            else (5 if variant == 'educational_negative' else 0)
        )
        record_property('authorization_negative_attempts', count)
        record_property('unauthorized_acceptances', 0)
        return
    if case == 'E21' and variant.startswith('preflight'):
        app, req = k.build(tuple(f's-{i:02d}' for i in range(16)), k=16)
        ids = k.approve(app, req)
        assert len(ids) == 16
        decision(app.check(req, ids), 'evidence_ready', 'structural_only')
        if variant == 'preflight17':
            decision(app.check(req, [None] * 17), 'resource_limit', 'reference_limit')
        return
    positive(monkeypatch)
    alternate = b.request(search_query='stair')
    app, c, ids = build((alternate,))
    with monkeypatch.context() as mp:
        observer = Observe(mp)
        try:
            handlers = {'E13': evaluate_e13, 'E14': evaluate_e14, 'E21': evaluate_e21}
            if case in handlers:
                handlers[case](app, c, ids, alternate, variant, observer)
            else:
                race(app, c, ids, alternate, variant, mp)
                observer.failed('view_fixture', 1) if variant == 'copy_first' else observer.failed('run', 0)
            record_property('guard_observations', observer.events)
        finally:
            observer.close()
    negative = {
        'E13': 1,
        'E14': 2 if variant in ('withdrawn_grant', 'audit_unavailable') else 1,
        'E15': 2 if variant == 'copy_first' else 3,
        'E21': 1,
    }[case]
    # Count target denials only; successful controls and setup are excluded.
    record_property('authorization_negative_attempts', negative)
    record_property('unauthorized_acceptances', 0)


def race(app, c, ids, alternate, variant, mp):
    d = held(app, c, ids)
    p = b.permit(app, d)
    queued, entered, resume = (threading.Event(), threading.Event(), threading.Event())
    original_lock = app._lock

    class QueueLock:
        def __enter__(self):
            if threading.current_thread().name == 'E46-writer':
                assert app._waiting > 0
                queued.set()
            original_lock.acquire()

        def __exit__(self, *args):
            original_lock.release()

    mp.setattr(app, '_lock', QueueLock())
    writes = []
    reads = []

    actions = {
        'attestation_writer_first': lambda: app.revoke('fixture-qr', ids[0]),
        'request_writer_first': lambda: app.update_request('fixture-ra', c, alternate),
        'source_writer_first': lambda: app.withdraw_source('fixture-ir', 's-a'),
        'copy_first': lambda: app.withdraw_source('fixture-ir', 's-a'),
    }
    writer = threading.Thread(target=lambda: writes.append(actions[variant]()), name='E46-writer')
    reader = None
    try:
        if variant == 'copy_first':
            original = app._valid

            def pause(*args):
                entered.set()
                assert resume.wait(3)
                return original(*args)

            mp.setattr(app, '_valid', pause)
            reader = threading.Thread(target=lambda: reads.append(app.view_fixture('fixture-pv', p)))
            reader.start()
            assert entered.wait(3)
            writer.start()
            assert queued.wait(3)
            resume.set()
            reader.join(3)
            writer.join(3)
            assert not reader.is_alive() and (not writer.is_alive())
            assert len(reads) == 1 and json.loads(reads[0])['text'] == H and (b.copies(app) == 1)
        else:
            with original_lock:
                writer.start()
                assert queued.wait(3)
                assert app.view_fixture('fixture-pv', p) == D and b.copies(app) == 0
            writer.join(3)
            assert not writer.is_alive()
        assert writes == ([c] if variant == 'request_writer_first' else [None])
        assert app.view_fixture('fixture-pv', p) == D and app.request_view('fixture-pv', d) == D
    finally:
        resume.set()
        for thread in (reader, writer):
            if thread is not None and thread.ident:
                thread.join(3)


def evaluate_preflight(case, variant):
    Time.current = (2026, 10, 20, 12, 0, 0)
    alt = (
        f.request(question='What code token describes a different fictional stair width?'),
        f.request(jurisdiction='Elsewhere'),
        f.request(edition='TEST-v2'),
    )
    control, req = f.build(variants=alt)
    key = f.approve(control, req)
    decision(control.check(req, [key]), 'evidence_ready', 'structural_only')
    app, req = f.build(variants=alt)
    if case == 'E11':
        evaluate_applicability(app, req, variant)
        return
    key = f.approve(app, req)
    decision(app.check(req, [key]), 'evidence_ready', 'structural_only')
    if variant == 'revoke_source':
        assert app.withdraw_source('TEST_ONLY-IR', 'test45f-code-control') is None
    elif variant == 'revoke_attestation':
        assert app.revoke('TEST_ONLY-QR', key) is None
    elif variant == 'change_question':
        req = alt[0]
    elif variant == 'change_jurisdiction':
        req = alt[1]
    elif variant == 'change_edition':
        req = alt[2]
    else:
        Time.current = (2026, 10, 22, 12, 0, 0)
    expected = next(
        x for c in CASES if c['case_id'] == case for x in c['variant_contracts'] if x['variant_id'] == variant
    )['expected']
    assert asdict(app.check(req, [key])) == expected
    return


def evaluate_applicability(app, req, variant):
    if variant == 'missing_question_approval':
        decision(app.check(req, []), 'evidence_gap', 'missing_applicability')
    elif variant == 'fictional_positive':
        decision(app.check(req, [f.approve(app, req)]), 'evidence_ready', 'structural_only')
    else:
        for topic, body in f.NOTES.items():
            metadata = f.meta(
                f'test45f-{topic}', body, reference=f'https://fixtures.invalid/{topic}', format='markdown'
            )
            req = f.request(scope='general', search_query='imaginary')
            a = kp.OfflineKnowledgePreflight(
                {t: p for t, p in f.CREDS.items() if p[1] in {'SA', 'IR', 'AP', 'QR'}},
                request_hashes=[kp.identity(asdict(req))],
                source_hashes={metadata.source_id: f.digest(body)},
            )
            p = a.propose_source('TEST_ONLY-SA', metadata)
            assert a.approve_source('TEST_ONLY-IR', metadata.source_id, p.document_id) is None
            assert a.ingest('TEST_ONLY-SA', metadata.source_id, body) is None
            decision(a.prepare(req), 'evidence_gap', 'unsupported_scope')
    return


def evaluate_e13(app, c, ids, alternate, variant, observer):
    if variant == 'forged_request_id':
        assert '0' * 32 not in app._authority.records
        assert app.prepare('fixture-qr', '0' * 32) == D
        observer.failed('current', 1)
    elif variant == 'forged_version':
        old = app._authority.records[c]
        app._authority.records[c] = replace(old, version=old.version + 1)
        assert app.prepare('fixture-qr', c) == D
        observer.failed('_context', 0)
    else:
        d = held(app, c, ids)
        p = b.permit(app, d)
        if variant == 'old_context_after_RA_update':
            assert app.update_request('fixture-ra', c, alternate) == c
            assert app._drafts[d].state == 'invalidated' and p not in app._permits
        elif variant == 'replayed_consumed_permit':
            copy(app, p, d)
            assert b.copies(app) == 1
        else:
            app = life.OfflinePrivateDraftLifecycle(
                b.CREDENTIALS,
                request_hashes=list(app._requests),
                source_hashes=app._preflight._sources,
                fixtures=app._fixtures,
            )
            assert not app._contexts and (not app._drafts) and (not app._permits)
        assert app.view_fixture('fixture-pv', p) == D
        observer.failed('view_fixture', 1)


def evaluate_e14(app, c, ids, alternate, variant, observer):
    d = held(app, c, ids, grant=variant != 'missing_grant')
    if variant == 'missing_grant':
        assert app.request_view('fixture-pv', d) == D
        observer.failed('_grant', 1)
    else:
        p = b.permit(app, d)
        if variant == 'authorized_fixture_copy':
            copy(app, p, d)
            assert b.copies(app) == 1
            assert app.view_fixture('fixture-pv', p) == D
            observer.failed('view_fixture', 1)
        elif variant == 'forged_reviewer':
            assert app.view_fixture('E46-forged-PV', p) == D
            observer.failed('_auth', 1)
            assert p in app._permits
        elif variant == 'withdrawn_grant':
            assert app.revoke_reviewer(d) is None and (not app._grants[d].active)
            assert p not in app._permits and app.view_fixture('fixture-pv', p) == D
            observer.failed('view_fixture', 1)
            observer.events.clear()
            assert app.request_view('fixture-pv', d) == D
            observer.failed('_grant', 1)
        elif variant == 'expired_permit':
            Time.current = (2026, 10, 16, 12, 0, 30)
            assert app.view_fixture('fixture-pv', p) == D
            observer.failed('view_fixture', 2)
        else:
            app._audit_available = False
            assert app.view_fixture('fixture-pv', p) == D
            observer.failed('audit_capacity_or_availability')
            assert not app._healthy
            app._audit_available = True
            assert app.request_view('fixture-pv', d) == D
    if variant != 'authorized_fixture_copy':
        assert b.copies(app) == 0


def evaluate_e21(app, c, ids, alternate, variant, observer):
    d = held(app, c, ids)
    if variant == 'request_context_cap':
        for _ in range(31):
            assert type(app.create_request('fixture-ra', b.request())) is str
        assert len(app._contexts) == 32 and app.create_request('fixture-ra', b.request()) == D
        observer.failed('create_request', 0)
        assert len(app._contexts) == 32
    elif variant == 'draft_cap':
        for _ in range(31):
            assert type(app.begin_fixture('f', c, ids)) is str
        assert len(app._drafts) == 32 and app.begin_fixture('f', c, ids) == D
        observer.failed('begin_fixture', 1)
        assert len(app._drafts) == 32
    elif variant == 'permit_cap':
        for _ in range(64):
            b.permit(app, d)
        assert app._permit_count == 64 and app.request_view('fixture-pv', d) == D
        observer.failed('request_view', 0)
        assert len(app._permits) == 64
    else:
        app._events = [life.AuditEvent(i + 1, app._session, '', 'test', 'intent') for i in range(2048)]
        assert app.begin_fixture('f', c, ids) == D and (not app._healthy)
        observer.failed('audit_capacity_or_availability')
        assert len(app._events) == 2048
