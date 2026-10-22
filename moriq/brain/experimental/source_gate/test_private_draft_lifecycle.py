"""Frozen B01-B44 plus request authority regressions; synthetic fixtures only."""

import ast
import datetime as dt
import hashlib
import json
import threading
from dataclasses import asdict, replace
from pathlib import Path
from unittest.mock import Mock

import private_draft_lifecycle as life
import pytest
from boundary import OfflinePrototype
from gateway import Gateway
from knowledge_preflight import BundleV1, RequestV1, canonical, identity

from moriq.knowledge.registry import SourceMetadata

ROOT = Path(__file__).parent
M = json.loads((ROOT / 'knowledge_preflight-v1.json').read_text())
SPEC = json.loads((ROOT / 'private_draft_lifecycle-v1.json').read_text())
F = SPEC['fixture_text']['F']
D = life.DENIED
REAL_DATE, REAL_TIME = dt.date, dt.datetime
CREDENTIALS = {f'fixture-{role.lower()}': (role, role) for role in ('SA', 'IR', 'AP', 'QR', 'PV', 'RA')}


class Date(REAL_DATE):
    @classmethod
    def today(cls):
        return cls(*Time.current[:3])


class Time(REAL_TIME):
    current = (2026, 10, 16, 12, 0, 0)

    @classmethod
    def now(cls, tz=None):
        return cls(*cls.current, tzinfo=tz)


@pytest.fixture(autouse=True)
def clock(monkeypatch):
    Time.current = (2026, 10, 16, 12, 0, 0)
    monkeypatch.setattr(dt, 'date', Date)
    monkeypatch.setattr(dt, 'datetime', Time)


def now():
    return Time.now(dt.UTC)


def advance(seconds):
    value = now() + dt.timedelta(seconds=seconds)
    Time.current = (value.year, value.month, value.day, value.hour, value.minute, value.second)


def request(**changes):
    return replace(RequestV1(M['question'], 'stair width', 'Testland-A', 'E1'), **changes)


def add(app, key, fixture):
    record = app.propose_source('fixture-sa', SourceMetadata(**fixture['metadata']))
    assert record != D
    assert app.approve_source('fixture-ir', key, record.document_id) is None
    assert app.ingest('fixture-sa', key, fixture['text'].encode()) is None


def approvals(app, context, *, count=None):
    bundle = app.prepare('fixture-qr', context)
    assert type(bundle) is BundleV1
    ids = []
    for entry in bundle.entries[:count]:
        key = app.propose_applicability(
            'fixture-ap', context, bundle, entry.alias, M['applicability'], Date(2026, 10, 17)
        )
        assert type(key) is str
        assert app.approve_applicability('fixture-qr', context, bundle, key) is None
        ids.append(key)
    return ids


def build(keys=('s-a',), *, variants=(), text=F, fixtures=None, k=5, approve=True, lease=True, expiry=600):
    fixtures = fixtures or {key: M['fixtures'][key] for key in keys}
    req = request(max_hits=k)
    aliases = tuple(str(i) for i in range(1, len(keys) + 1))
    catalog = {
        'f': life.Fixture(identity(asdict(req)), tuple(keys), text, aliases, hashlib.sha256(text.encode()).hexdigest())
    }
    app = life.OfflinePrivateDraftLifecycle(
        CREDENTIALS,
        request_hashes=[identity(asdict(r)) for r in (req, *variants)],
        source_hashes={key: f['metadata']['content_sha256'] for key, f in fixtures.items()},
        fixtures=catalog,
    )
    context = app.create_request('fixture-ra', req)
    assert type(context) is str
    for key in keys:
        add(app, key, fixtures[key])
    ids = approvals(app, context) if approve else []
    if lease:
        for key in keys:
            assert app.lease_source('fixture-ir', context, key, now() + dt.timedelta(seconds=expiry)) is None
    return app, context, ids


def held(app, context, ids):
    key = app.begin_fixture('f', context, ids)
    assert type(key) is str, key
    assert app.complete_fixture(key) == key
    assert app.grant_reviewer(key, now() + dt.timedelta(seconds=600)) is None
    return key


def permit(app, key):
    value = app.request_view('fixture-pv', key)
    assert type(value) is str, value
    return value


def success(app, token, text=F):
    payload = app.view_fixture('fixture-pv', token)
    data = json.loads(payload)
    assert data == dict(
        status='private_draft',
        synthetic=True,
        claim_status='not_assessed',
        release_allowed=False,
        text=text,
        aliases=list(app._fixtures['f'].aliases),
        draft_id=data['draft_id'],
    )
    assert payload == canonical(data).encode()
    assert app.public_result() == b'{"status":"withheld","release_allowed":false}'
    return data


def copies(app):
    return sum(e.action == 'private_copy' and e.result == 'committed' for e in app._events)


def test_B01():
    app, c, ids = build()
    p = permit(app, held(app, c, ids))
    success(app, p)
    assert app.view_fixture('fixture-pv', p) == D and copies(app) == 1


@pytest.mark.parametrize('token', ['wrong', 'PV', 'fixture-sa', 'fixture-ir', 'fixture-ap', 'fixture-qr'])
def test_B02(token, monkeypatch):
    app, c, ids = build()
    p = permit(app, held(app, c, ids))
    with monkeypatch.context() as mp:
        mp.setattr(life, 'canonical', Mock(side_effect=AssertionError('serialization before auth')))
        assert app.view_fixture(token, p) == D
    assert p in app._permits and copies(app) == 0


@pytest.mark.parametrize('other', [False, True])
def test_B03(other):
    app, c, ids = build()
    key = app.begin_fixture('f', c, ids)
    assert app.complete_fixture(key) == key
    if other:
        held(app, c, ids)
    assert app.request_view('fixture-pv', key) == D and app._permit_count == 0


@pytest.mark.parametrize('revoke', [True, False])
def test_B04(revoke):
    app, c, ids = build()
    key = held(app, c, ids)
    p = permit(app, key)
    if revoke:
        app.revoke_reviewer(key)
    else:
        app.grant_reviewer(key, now() + dt.timedelta(seconds=600))
    assert app.view_fixture('fixture-pv', p) == D and copies(app) == 0


def test_B05():
    app, c, ids = build()
    key = app.begin_fixture('f', c, ids)
    app.withdraw_source('fixture-ir', 's-a')
    assert app.complete_fixture(key) == D
    assert app._drafts[key].state == 'invalidated' and app._drafts[key].text == ''
    assert app.request_view('fixture-pv', key) == D


@pytest.mark.parametrize('state', ['retired', 'superseded'])
def test_B06(state):
    app, c, ids = build()
    key = held(app, c, ids)
    app.withdraw_source('fixture-ir', 's-a', state)
    assert app.request_view('fixture-pv', key) == D
    assert app._drafts[key].state == 'invalidated'


def test_B07():
    app, c, ids = build()
    p = permit(app, held(app, c, ids))
    app.revoke('fixture-qr', ids[0])
    assert app.view_fixture('fixture-pv', p) == D and copies(app) == 0


def test_B08():
    app, c, ids = build()
    key = held(app, c, ids)
    p = permit(app, key)
    newer = approvals(app, c)
    assert app.supersede('fixture-qr', ids[0], newer[0]) is None
    assert app.view_fixture('fixture-pv', p) == D
    assert app.request_view('fixture-pv', key) == D
    success(app, permit(app, held(app, c, newer)))


@pytest.mark.parametrize('expired', [False, True])
def test_B09(expired):
    app, c, ids = build(lease=expired)
    if expired:
        advance(600)
    assert app.begin_fixture('f', c, ids) == D


def test_B10():
    app, c, ids = build(expiry=3 * 86400)
    Time.current = (2026, 10, 17, 12, 0, 0)
    success(app, permit(app, held(app, c, ids)))
    Time.current = (2026, 10, 18, 12, 0, 0)
    assert app.begin_fixture('f', c, ids) == D


@pytest.mark.parametrize('seconds', [29, 30])
def test_B11(seconds):
    app, c, ids = build()
    p = permit(app, held(app, c, ids))
    advance(seconds)
    if seconds == 29:
        success(app, p)
    else:
        assert app.view_fixture('fixture-pv', p) == D


def test_B12():
    app, c, ids = build()
    key = held(app, c, ids)
    advance(300)
    assert app.request_view('fixture-pv', key) == D
    assert app._drafts[key].state == 'invalidated'


@pytest.mark.parametrize('q', [M['question'] + ' ', M['question'].upper(), M['question'] + '!'])
def test_B13(q):
    other = request(question=q)
    app, c, ids = build(variants=(other,))
    key = held(app, c, ids)
    p = permit(app, key)
    assert app.update_request('fixture-ra', c, other) == c
    assert app.view_fixture('fixture-pv', p) == D and app.request_view('fixture-pv', key) == D


@pytest.mark.parametrize('changes', [{'jurisdiction': 'Testland-B'}, {'edition': 'E2'}])
def test_B14(changes):
    other = request(**changes)
    app, c, ids = build(variants=(other,))
    p = permit(app, held(app, c, ids))
    app.update_request('fixture-ra', c, other)
    assert app.view_fixture('fixture-pv', p) == D


def test_B15():
    other = request(search_query='stair')
    app, c, ids = build(variants=(other,))
    p = permit(app, held(app, c, ids))
    app.update_request('fixture-ra', c, other)
    assert app.view_fixture('fixture-pv', p) == D


def test_B16():
    app, c, ids = build()
    key = held(app, c, ids)
    add(app, 's-a', M['fixtures']['s-a'])
    assert app.request_view('fixture-pv', key) == D


@pytest.mark.parametrize(
    'changes', [{'text': 'changed'}, {'content_sha256': '0' * 64}, {'start': 1}, {'source_id': 's-b'}]
)
def test_B17(changes):
    app, c, ids = build()
    p = permit(app, held(app, c, ids))
    registry = app._preflight._registry
    registry._chunks['s-a'] = (replace(registry.chunks()[0], **changes),)
    assert app.view_fixture('fixture-pv', p) == D and copies(app) == 0


@pytest.mark.parametrize('text', ['tampered', F.replace('[1]', '[99]')])
def test_B18(text):
    app, c, ids = build()
    key = held(app, c, ids)
    p = permit(app, key)
    app._drafts[key] = replace(app._drafts[key], text=text)
    assert app.view_fixture('fixture-pv', p) == D


def test_B19():
    app, c, ids = build()
    key = held(app, c, ids)
    p = permit(app, key)
    fresh = life.OfflinePrivateDraftLifecycle(
        CREDENTIALS,
        request_hashes=list(app._requests),
        source_hashes={'s-a': M['fixtures']['s-a']['metadata']['content_sha256']},
        fixtures=app._fixtures,
    )
    assert fresh._drafts == {} and fresh._contexts == {}
    assert fresh.complete_fixture(key) == D
    assert fresh.request_view('fixture-pv', key) == D
    assert fresh.view_fixture('fixture-pv', p) == D
    assert fresh.begin_fixture('f', c, ids) == D
    new, nc, _ = build()
    assert new.begin_fixture('f', nc, ids) == D


def test_B20():
    app, c, ids = build()
    key = held(app, c, ids)
    assert app.complete_fixture(key) == D
    p = permit(app, key)
    success(app, p)
    assert app.view_fixture('fixture-pv', p) == D
    assert copies(app) == 1
    assert sum(e.action == 'retain' for e in app._events) == 1


def test_B21():
    app, c, _ = build(('s-a', 's-b'), text=SPEC['fixture_text']['M'], approve=False)
    ids = approvals(app, c, count=1)
    assert app.begin_fixture('f', c, ids) == D and not app._drafts


def test_B22():
    text = SPEC['fixture_text']['M']
    app, c, ids = build(('s-a', 's-b'), text=text)
    key = held(app, c, ids)
    assert len(app._drafts[key].versions) == 2
    success(app, permit(app, key), text)


@pytest.mark.parametrize('variant', ['mode', 'exercise', 'reviewed', 'mixed', 'real'])
def test_B23(variant):
    app, c, ids = build(('s-a', 's-b'), text=SPEC['fixture_text']['M']) if variant == 'mixed' else build()
    if variant in {'mode', 'exercise', 'reviewed'}:
        assert app.create_request('fixture-ra', dict(asdict(request()), **{variant: True})) == D
    elif variant == 'real':
        assert app.begin_fixture('real-document', c, ids) == D
    else:
        # Test-only hostile signed record, as in unchanged preflight binding regressions.
        boundary = app._preflight._attestations
        record = boundary.inspect('fixture-qr', ids[1])
        key = boundary.create(
            'fixture-ap',
            document=record.document,
            question=record.question,
            kind='code',
            provenance=record.review.provenance,
            applicability=M['applicability'],
            jurisdiction='Testland-A',
            edition='E1',
            expires_on=Date(2026, 10, 17),
        )
        boundary.approve('fixture-qr', key)
        assert app.begin_fixture('f', c, [ids[0], key]) == D
    assert copies(app) == 0


def test_B24(monkeypatch, capsys):
    app, c, ids = build(('s-inject',))
    forbidden = tripwires(monkeypatch)
    success(app, permit(app, held(app, c, ids)))
    forbidden.assert_not_called()
    assert capsys.readouterr() == ('', '')


def test_B25():
    text = SPEC['fixture_text']['X']
    app, c, ids = build(text=text)
    success(app, permit(app, held(app, c, ids)), text)
    assert text.encode() not in app.public_result()


def test_B26():
    test_B22()
    test_B21()


def test_B27():
    app, c, ids = build()
    p = permit(app, held(app, c, ids))
    done = threading.Event()
    writer = threading.Thread(target=lambda: (app.withdraw_source('fixture-ir', 's-a'), done.set()))
    writer.start()
    assert done.wait(3)
    assert app.view_fixture('fixture-pv', p) == D and copies(app) == 0
    writer.join(3)


def race(monkeypatch, action):
    app, c, ids = build(variants=(request(search_query='stair'),))
    key = held(app, c, ids)
    p = permit(app, key)
    entered, resume, waiting, done = (threading.Event() for _ in range(4))
    old = app._valid

    def pause(*args):
        entered.set()
        assert resume.wait(3)
        return old(*args)

    monkeypatch.setattr(app, '_valid', pause)
    results = []
    reader = threading.Thread(target=lambda: results.append(app.view_fixture('fixture-pv', p)))
    reader.start()
    assert entered.wait(3)

    def write():
        waiting.set()
        action(app, c)
        done.set()

    writer = threading.Thread(target=write)
    writer.start()
    assert waiting.wait(3) and not done.wait(0.05)
    resume.set()
    reader.join(3)
    writer.join(3)
    assert not reader.is_alive() and not writer.is_alive() and done.is_set()
    assert json.loads(results[0])['status'] == 'private_draft' and copies(app) == 1
    monkeypatch.setattr(app, '_valid', old)
    assert app.request_view('fixture-pv', key) == D


def test_B28(monkeypatch):
    race(monkeypatch, lambda app, _: app.withdraw_source('fixture-ir', 's-a'))


def test_B29(monkeypatch):
    race(
        monkeypatch, lambda app, _: app.propose_source('fixture-sa', SourceMetadata(**M['fixtures']['s-a']['metadata']))
    )


@pytest.mark.parametrize('variant', ['rollback', 'dates', 'rollover'])
def test_B30(variant, monkeypatch):
    app, c, ids = build()
    p = permit(app, held(app, c, ids))
    if variant == 'rollback':
        advance(-1)
    elif variant == 'dates':
        monkeypatch.setattr(Date, 'today', classmethod(lambda cls: cls(2026, 10, 15)))
    else:
        old = app._valid

        def rollover(*args):
            result = old(*args)
            advance(86400)
            return result

        monkeypatch.setattr(app, '_valid', rollover)
    assert app.view_fixture('fixture-pv', p) == D and not app._healthy
    Time.current = (2026, 10, 16, 12, 0, 0)
    assert app.begin_fixture('f', c, ids) == D


@pytest.mark.parametrize('begin', [True, False])
def test_B31(begin):
    app, c, ids = build()
    p = None if begin else permit(app, held(app, c, ids))
    app._audit_available = False
    assert (app.begin_fixture('f', c, ids) if begin else app.view_fixture('fixture-pv', p)) == D
    assert not app._healthy and copies(app) == 0
    app._audit_available = True
    assert app.begin_fixture('f', c, ids) == D


@pytest.mark.parametrize('after_append', [True, False])
def test_B32(after_append, monkeypatch, capsys):
    app, c, ids = build()
    p = permit(app, held(app, c, ids))
    old = app._audit

    def fail(*args):
        if after_append:
            old(*args)
        raise RuntimeError('PRIVATE_SENTINEL')

    monkeypatch.setattr(app, '_audit', fail)
    assert app.view_fixture('fixture-pv', p) == D
    assert not app._healthy and copies(app) == 0 and capsys.readouterr() == ('', '')


def test_B33(monkeypatch):
    app, c, ids = build()
    p = permit(app, held(app, c, ids))
    app._auth_available = False
    forbidden = Mock(side_effect=AssertionError('serialize'))
    monkeypatch.setattr(life, 'canonical', forbidden)
    assert app.view_fixture('fixture-pv', p) == D
    forbidden.assert_not_called()


@pytest.mark.parametrize('replay', [False, True])
def test_B34(replay):
    app, c, ids = build()
    p = permit(app, held(app, c, ids))
    boundary = app._preflight._attestations
    saved = boundary._records[ids[0]]
    if replay:
        boundary.revoke('fixture-qr', ids[0])
        boundary._records[ids[0]] = saved
    else:
        boundary._records[ids[0]] = (saved[0], '0' * 64)
    assert app.view_fixture('fixture-pv', p) == D


def sixteen():
    keys = tuple(f's-{i:02d}' for i in range(16))
    text = 'SYNTHETIC TEST ONLY: Compare these fictional passages ' + ' '.join(f'[{i}]' for i in range(1, 17)) + '.'
    return keys, text


def test_B35(monkeypatch):
    keys, text = sixteen()
    app, c, ids = build(keys, text=text, k=16)
    key = app.begin_fixture('f', c, ids)
    assert type(key) is str and len(app._drafts[key].ids) == 16
    forbidden = Mock(side_effect=AssertionError('per-reference work'))
    monkeypatch.setattr(app, '_binding', forbidden)
    assert app.begin_fixture('f', c, [None] * 17) == D
    forbidden.assert_not_called()


@pytest.mark.parametrize('size', [65536, 65537])
def test_B36_text(size):
    app, c, ids = build(text=F + ' ' * (65536 - len(F.encode())))
    if size == 65537:
        fixture = app._fixtures['f']
        app._fixtures['f'] = replace(
            fixture, text=fixture.text + ' ', sha256=hashlib.sha256((fixture.text + ' ').encode()).hexdigest()
        )
        assert app.begin_fixture('f', c, ids) == D
        assert not app._drafts
    else:
        success(app, permit(app, held(app, c, ids)), app._fixtures['f'].text)


@pytest.mark.parametrize('size', [65536, 65537])
def test_B36_bundle(size):
    keys, text = sixteen()
    app, c, _ = build(keys, text=text, k=16, approve=False)
    bundle = app.prepare('fixture-qr', c)
    remaining = size - len(canonical(asdict(bundle)).encode())
    fixtures = {key: dict(M['fixtures'][key], metadata=dict(M['fixtures'][key]['metadata'])) for key in keys}
    for fixture in fixtures.values():
        for field in ('title', 'publisher', 'author'):
            old = fixture['metadata'][field]
            extra = min(2048 - len(old), remaining)
            fixture['metadata'][field] += 'x' * extra
            remaining -= extra
    assert remaining == 0
    if size == 65536:
        app, c, ids = build(keys, fixtures=fixtures, text=text, k=16)
        assert len(canonical(asdict(app.prepare('fixture-qr', c))).encode()) == size
        assert type(app.begin_fixture('f', c, ids)) is str
    else:
        app, c, _ = build(keys, fixtures=fixtures, text=text, k=16, approve=False, lease=False)
        assert app.begin_fixture('f', c, ['0' * 32]) == D
        assert not app._drafts


@pytest.mark.parametrize('budget', ['drafts', 'permits', 'operations', 'audit'])
def test_B37(budget):
    app, c, ids = build()
    key = held(app, c, ids)
    if budget == 'drafts':
        for _ in range(31):
            assert type(app.begin_fixture('f', c, ids)) is str
        assert len(app._drafts) == 32 and app.begin_fixture('f', c, ids) == D
    elif budget == 'permits':
        for _ in range(64):
            permit(app, key)
        assert app._permit_count == 64 and app.request_view('fixture-pv', key) == D
    elif budget == 'operations':
        while app._operations < 256:
            app.update_request('fixture-ra', c, request())
        assert app.begin_fixture('f', c, ids) == D and app._operations == 256
    else:
        app._events = [life.AuditEvent(i + 1, app._session, '', 'test', 'intent') for i in range(2048)]
        assert app.begin_fixture('f', c, ids) == D and not app._healthy and len(app._events) == 2048


def test_B38(monkeypatch):
    app, c, ids = build()
    key = held(app, c, ids)
    p, second = permit(app, key), permit(app, key)
    entered, resume = threading.Event(), threading.Event()
    old = app._valid

    def pause(*args):
        entered.set()
        assert resume.wait(3)
        return old(*args)

    monkeypatch.setattr(app, '_valid', pause)
    results = []
    reader = threading.Thread(target=lambda: results.append(app.view_fixture('fixture-pv', p)))
    reader.start()
    assert entered.wait(3)
    assert app.view_fixture('fixture-pv', second) == D
    resume.set()
    reader.join(3)
    assert not reader.is_alive() and json.loads(results[0])['status'] == 'private_draft'
    assert app.withdraw_source('fixture-ir', 's-a') is None


@pytest.mark.parametrize('where', ['fixture', 'source', 'exception'])
def test_B39(where, monkeypatch, capsys):
    text = F + ' PRIVATE_SENTINEL' if where == 'fixture' else F
    fixtures = None
    if where == 'source':
        source = M['fixtures']['s-a']['text'] + ' PRIVATE_SENTINEL'
        fixtures = {
            's-a': dict(
                text=source,
                metadata=dict(
                    M['fixtures']['s-a']['metadata'], content_sha256=hashlib.sha256(source.encode()).hexdigest()
                ),
            )
        }
    app, c, ids = build(text=text, fixtures=fixtures)
    key = held(app, c, ids)
    p = permit(app, key)
    assert 'PRIVATE_SENTINEL' not in repr(app._drafts) + repr(app._fixtures) + repr(app._authority)
    if where == 'exception':
        monkeypatch.setattr(app, '_valid', Mock(side_effect=RuntimeError('PRIVATE_SENTINEL')))
        assert app.view_fixture('fixture-pv', p) == D
    else:
        success(app, p, text)
    assert app.view_fixture('wrong', 'unknown') == D
    assert b'PRIVATE_SENTINEL' not in app.public_result() + D
    assert 'PRIVATE_SENTINEL' not in repr(app._events)
    assert capsys.readouterr() == ('', '')


def test_B40():
    expected = None
    for _ in range(100):
        app, c, ids = build()
        p = permit(app, held(app, c, ids))
        result = success(app, p)
        result.pop('draft_id')
        expected = result if expected is None else expected
        assert result == expected and app.view_fixture('fixture-pv', p) == D
        assert app.public_result() == life.WITHHELD


def tripwires(monkeypatch):
    import socket
    import subprocess
    import urllib.request

    from mock_harness import MockHarness

    forbidden = Mock(side_effect=AssertionError('Forbidden invocation'))
    for owner, attr in (
        (Gateway, 'respond'),
        (Gateway, 'hold'),
        (OfflinePrototype, 'public'),
        (OfflinePrototype, 'view'),
        (MockHarness, 'public'),
        (MockHarness, '_run_worker'),
        (socket, 'socket'),
        (socket, 'create_connection'),
        (subprocess, 'Popen'),
        (urllib.request, 'urlopen'),
    ):
        monkeypatch.setattr(owner, attr, forbidden)
    return forbidden


def test_B41(monkeypatch):
    forbidden = tripwires(monkeypatch)
    app, c, ids = build()
    app._preflight._attestations._generate = forbidden
    key = held(app, c, ids)
    success(app, permit(app, key))
    app.revoke('fixture-qr', ids[0])
    assert app.request_view('fixture-pv', key) == D
    forbidden.assert_not_called()
    tree = ast.parse(Path(life.__file__).read_text())
    prohibited = {'respond', 'hold', 'public', 'view', '_run_worker', '_seal', '_load', '_current'}
    assert not any(
        isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in prohibited
        for n in ast.walk(tree)
    )
    assert not any(
        isinstance(n, ast.Attribute) and n.attr in {'_registry', '_attestations', '_key', '_records'}
        for n in ast.walk(tree)
    )


def test_B42():
    app, c, ids = build()
    changed = dict(CREDENTIALS, **{'fixture-qr': ('AP', 'QR')})
    with pytest.raises(ValueError):
        life.OfflinePrivateDraftLifecycle(changed, request_hashes=[], source_hashes={}, fixtures={})
    assert app.begin_fixture('f', c, []) == D
    for source, chunk, attestation in [('fake', None, None), (None, 'fake', None), (None, None, '0' * 32)]:
        other, oc, oi = build()
        if attestation:
            assert other.begin_fixture('f', oc, [attestation]) == D
        else:
            registry = other._preflight._registry
            record = registry.chunks()[0]
            registry._chunks['s-a'] = (replace(record, **({'source_id': source} if source else {'chunk_id': chunk})),)
            assert other.begin_fixture('f', oc, oi) == D


def test_B43(monkeypatch):
    app, c, ids = build(expiry=20)
    p = permit(app, held(app, c, ids))
    advance(19)
    old = app._audit

    def boundary(*args):
        old(*args)
        advance(1)

    monkeypatch.setattr(app, '_audit', boundary)
    assert app.view_fixture('fixture-pv', p) == D and copies(app) == 0


@pytest.mark.parametrize('change', ['lease', 'grant', 'restore'])
def test_B44(change):
    app, c, ids = build()
    key = held(app, c, ids)
    p = permit(app, key)
    if change == 'lease':
        app.lease_source('fixture-ir', c, 's-a', now() + dt.timedelta(seconds=700))
    elif change == 'grant':
        app.grant_reviewer(key, now() + dt.timedelta(seconds=700))
    else:
        app.withdraw_source('fixture-ir', 's-a')
        add(app, 's-a', M['fixtures']['s-a'])
    assert app.view_fixture('fixture-pv', p) == D
    if change == 'grant':
        success(app, permit(app, key))
    else:
        assert app.request_view('fixture-pv', key) == D


def test_frozen_spec():
    assert [c['id'] for c in SPEC['cases']] == [f'B{i:02d}' for i in range(1, 45)]
    assert (
        hashlib.sha256((ROOT / 'knowledge_preflight-v1.json').read_bytes()).hexdigest()
        == SPEC['preflight_manifest_sha256']
    )


@pytest.mark.parametrize('token', ['PV', 'wrong', 'fixture-pv', 'fixture-ap', 'fixture-qr', 'fixture-ir', 'fixture-sa'])
def test_request_update_requires_authority(token):
    other = request(search_query='stair')
    app, c, ids = build(variants=(other,))
    p = permit(app, held(app, c, ids))
    assert app.update_request(token, c, other) == D
    assert app._authority.current(c).version == 1
    success(app, p)


@pytest.mark.parametrize('field', ['version', 'hash', 'missing', 'unavailable'])
def test_request_state_integrity(field):
    app, c, ids = build()
    p = permit(app, held(app, c, ids))
    old = app._authority.current(c)
    if field == 'version':
        app._authority.records[c] = replace(old, version=old.version + 1)
    elif field == 'hash':
        app._authority.records[c] = replace(old, content_hash='0' * 64)
    elif field == 'missing':
        del app._authority.records[c]
    else:
        app._authority.available = False
    assert app.view_fixture('fixture-pv', p) == D


def test_request_metadata_not_authority():
    app, c, ids = build()
    p = permit(app, held(app, c, ids))
    assert (
        app.update_request('fixture-ra', c, dict(asdict(request()), version=2, content_hash='0' * 64, approved=True))
        == D
    )
    success(app, p)


def test_request_same_value_and_other_context():
    other = request(search_query='stair')
    app, c, ids = build(variants=(other,))
    p = permit(app, held(app, c, ids))
    assert app.update_request('fixture-ra', c, request()) == c
    second = app.create_request('fixture-ra', request())
    assert app.update_request('fixture-ra', second, other) == second
    assert app._authority.current(c).version == 1 and app._authority.current(second).version == 2
    success(app, p)


def test_request_update_view_order(monkeypatch):
    race(monkeypatch, lambda app, c: app.update_request('fixture-ra', c, request(search_query='stair')))
