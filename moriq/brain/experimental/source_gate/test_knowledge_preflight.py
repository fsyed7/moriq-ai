"""Frozen K01-K52: synthetic, independent approval, no adapter execution."""

import ast
import datetime as dt
import hashlib
import json
import threading
from dataclasses import asdict, replace
from pathlib import Path
from unittest.mock import Mock

import knowledge_preflight as kp
import pytest
from boundary import OfflinePrototype
from gateway import Document, Draft, Gateway, citations_valid

from moriq.knowledge.registry import SourceMetadata, task3_attestation_adapter

M = json.loads(Path(__file__).with_name('knowledge_preflight-v1.json').read_text())
REAL_DATE, REAL_TIME = dt.date, dt.datetime
CREDENTIALS = {x.lower(): (x, x) for x in ('SA', 'IR', 'AP', 'QR')}
CREDENTIALS['ap-alias'] = ('AP', 'AP')


class FixedDate(REAL_DATE):
    current = (2026, 10, 16)

    @classmethod
    def today(cls):
        return cls(*cls.current)


class FixedTime(REAL_TIME):
    @classmethod
    def now(cls, tz=None):
        return cls(2026, 10, 16, tzinfo=tz)


@pytest.fixture(autouse=True)
def fixed_time(monkeypatch):
    FixedDate.current = (2026, 10, 16)
    monkeypatch.setattr(dt, 'date', FixedDate)
    monkeypatch.setattr(dt, 'datetime', FixedTime)


def request(**changes):
    return replace(kp.RequestV1(M['question'], 'stair width', 'Testland-A', 'E1'), **changes)


def independent_hash(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()
    ).hexdigest()


def build(keys=('s-a',), *, requests=(), fixtures=None, k=5):
    fixtures = fixtures or M['fixtures']
    req = request(max_hits=k)
    app = kp.OfflineKnowledgePreflight(
        CREDENTIALS,
        request_hashes=[independent_hash(asdict(x)) for x in (req, *requests)],
        source_hashes={key: f['metadata']['content_sha256'] for key, f in fixtures.items()},
    )
    app._attestations._generate = Mock(side_effect=AssertionError('Forbidden generator'))
    for key in keys:
        add(app, key, fixtures[key])
    return app, req


def add(app, key, fixture):
    record = app.propose_source('sa', SourceMetadata(**fixture['metadata']))
    assert not isinstance(record, kp.Decision), record
    if 'document_id' in fixture:
        assert record.document_id == fixture['document_id']
    assert app.approve_source('ir', key, record.document_id) is None
    assert app.ingest('sa', key, fixture['text'].encode()) is None


def approve(app, req, *, bundle=None, pending=False):
    bundle = bundle or app.prepare(req)
    assert type(bundle) is kp.BundleV1, bundle
    keys = []
    for entry in bundle.entries:
        key = app.propose_applicability('ap', req, bundle, entry.alias, M['applicability'], FixedDate(2026, 10, 17))
        assert type(key) is str, key
        if not pending:
            assert app.approve_applicability('qr', req, bundle, key) is None
        keys.append(key)
    return keys


def outcome(result, reason='structural_only', status=None):
    if status is None:
        status = 'evidence_ready' if reason == 'structural_only' else 'evidence_gap'
    assert type(result) is kp.Decision
    assert asdict(result) == dict(status=status, reason=reason, claim_status='not_assessed', release_allowed=False)


def check(app, req, ids, reason='structural_only', status=None):
    result = app.check(req, ids)
    outcome(result, reason, status)
    app._attestations._generate.assert_not_called()
    assert app._attestations._drafts == []
    return result


def signed(app, bundle, entry, **changes):
    args = dict(
        document=Document(entry.alias, entry.text),
        question=bundle.request.question,
        kind='fictional',
        provenance=kp.binding(bundle, entry),
        applicability=M['applicability'],
        jurisdiction=bundle.request.jurisdiction,
        edition=bundle.request.edition,
        expires_on=FixedDate(2026, 10, 17),
    )
    args.update(changes)
    key = app._attestations.create('ap', **args)
    app._attestations.approve('qr', key)
    return key


def test_K01():
    app, req = build()
    bundle = app.prepare(req)
    entry = bundle.entries[0]
    assert entry.alias == '1' and entry.chunk_id == M['fixtures']['s-a']['chunk_id']
    assert entry.document_id == M['fixtures']['s-a']['document_id']
    assert entry.start == 0 and entry.end == len(entry.text)
    assert asdict(entry.provenance.metadata) == M['fixtures']['s-a']['metadata']
    assert entry.provenance.lifecycle == 'active' and entry.provenance.review_status == 'approved'
    assert entry.chunk_sha256 == hashlib.sha256(entry.text.encode()).hexdigest()
    assert bundle.bundle_id == independent_hash(asdict(bundle))
    check(app, req, approve(app, req))


def test_K02():
    app, req = build()
    check(app, req, [], 'missing_applicability')
    assert app._attestations.audit('qr') == ()


def test_K03():
    app, req = build()
    check(app, req, approve(app, req, pending=True), 'stale_attestation')


def test_K04():
    app, req = build()
    for name in ('reviewed', 'reviewer'):
        check(app, dict(asdict(req), **{name: True}), ['0' * 32], 'schema', 'invalid_request')


def test_K05():
    app, req = build()
    bundle = app.prepare(req)
    ids = approve(app, req, pending=True)
    for token in ('wrong', 'ir', 'sa', 'ap', 'ap-alias'):
        with pytest.raises(PermissionError):
            app.approve_applicability(token, req, bundle, ids[0])
        check(app, req, ids, 'stale_attestation')


def test_K06():
    app, req = build()
    bundle = app.prepare(req)
    forged = replace(bundle, entries=(replace(bundle.entries[0], source_id='forged'),))
    outcome(
        app.propose_applicability('ap', req, forged, '1', M['applicability'], FixedDate(2026, 10, 17)),
        'binding_mismatch',
    )
    assert app._attestations.audit('qr') == ()


def test_K07():
    app, req = build()
    bundle = app.prepare(req)
    for changes in ({'chunk_id': '0' * 64}, {'source_id': 's-b', 'chunk_id': M['fixtures']['s-b']['chunk_id']}):
        forged = replace(bundle, entries=(replace(bundle.entries[0], **changes),))
        outcome(
            app.propose_applicability('ap', req, forged, '1', M['applicability'], FixedDate(2026, 10, 17)),
            'binding_mismatch',
        )


def test_K08():
    for changes in ({'text': 'tampered'}, {'content_sha256': '0' * 64}, {'start': 1}):
        app, req = build()
        ids = approve(app, req)
        app._registry._chunks['s-a'] = (replace(app._registry.chunks()[0], **changes),)
        check(app, req, ids, 'integrity_failure')


def text_fixture(text):
    return {
        'text': text,
        'metadata': dict(M['fixtures']['s-a']['metadata'], content_sha256=hashlib.sha256(text.encode()).hexdigest()),
    }


def test_K09():
    text = 'Synthetic stair width. ' * 90
    app, req = build(fixtures={'s-a': text_fixture(text)})
    bundle = app.prepare(req)
    ids = []
    for e in bundle.entries:
        # Existing create hashes the submitted full document, not the selected chunk.
        key = signed(app, bundle, e, document=Document(e.alias, text))
        assert app._attestations.inspect('qr', key).review.content_sha256 == e.document_sha256
        ids.append(key)
    check(app, req, ids, 'binding_mismatch')


def test_K10():
    app, req = build()
    ids = approve(app, req)
    app.revoke('qr', ids[0])
    check(app, req, ids, 'stale_attestation')


def test_K11():
    app, req = build()
    old = approve(app, req)
    new = approve(app, req)
    app.supersede('qr', old[0], new[0])
    check(app, req, old, 'stale_attestation')
    check(app, req, new)


def test_K12():
    app, req = build()
    ids = approve(app, req)
    FixedDate.current = (2026, 10, 18)
    check(app, req, ids, 'stale_attestation')


def test_K13():
    for state in ('revoked', 'retired', 'superseded'):
        app, req = build()
        bundle = app.prepare(req)
        ids = approve(app, req)
        app.withdraw_source('ir', 's-a', state)
        check(app, req, ids, 'no_evidence')
        outcome(
            app.propose_applicability('ap', req, bundle, '1', M['applicability'], FixedDate(2026, 10, 17)),
            'stale_source',
        )


def test_K14():
    app, req = build()
    ids = approve(app, req)
    old = app.prepare(req)
    f = dict(M['fixtures']['s-a'])
    f.pop('document_id')
    add(app, 's-a', f)
    assert old.entries[0].document_id != app.prepare(req).entries[0].document_id
    check(app, req, ids, 'binding_mismatch')


def test_K15():
    other = request(jurisdiction='Testland-B')
    app, req = build(requests=(other,))
    check(app, other, approve(app, req), 'no_evidence')


def test_K16():
    other = request(edition='E2')
    app, req = build(requests=(other,))
    check(app, other, approve(app, req), 'no_evidence')


def test_K17():
    for changes in ({'jurisdiction': 'Testland-B'}, {'edition': 'E2'}):
        app, req = build()
        b = app.prepare(req)
        check(app, req, [signed(app, b, b.entries[0], **changes)], 'binding_mismatch')


def test_K18():
    for q in (M['question'] + ' ', M['question'] + '!', M['question'].upper()):
        other = request(question=q)
        app, req = build(requests=(other,))
        check(app, other, approve(app, req), 'binding_mismatch')


def test_K19():
    other = request(search_query='stair')
    app, req = build(requests=(other,))
    check(app, other, approve(app, req), 'binding_mismatch')


def test_K20(capsys):
    app, req = build(('s-inject',))
    check(app, req, approve(app, req))
    assert app.prepare(req).entries[0].text == M['fixtures']['s-inject']['text']
    assert capsys.readouterr() == ('', '')


def test_K21():
    app, req = build(('s-a', 's-b'))
    b = app.prepare(req)
    assert [(e.alias, e.source_id) for e in b.entries] == [('1', 's-a'), ('2', 's-b')]
    check(app, req, approve(app, req))


def test_K22():
    app, req = build(('s-a', 's-b'))
    check(app, req, approve(app, req)[:1], 'missing_applicability')


def test_K23():
    app, req = build(('s-a', 's-c'))
    b = app.prepare(req)
    other, other_req = build(('s-c',))
    wrong = other.prepare(other_req)
    check(app, req, [signed(app, wrong, wrong.entries[0])], 'binding_mismatch')
    assert len(b.entries) == 1


def test_K24():
    app, req = build(('s-a', 's-b'))
    b = app.prepare(req)
    keys = [signed(app, b, replace(e, alias=str(3 - int(e.alias)))) for e in b.entries]
    check(app, req, keys, 'binding_mismatch')
    other, r = build()
    other_b = other.prepare(r)
    check(app, req, [signed(app, other_b, other_b.entries[0]), keys[1]], 'binding_mismatch')


def test_K25():
    app, req = build()
    check(app, req, ['0' * 32], 'missing_applicability')


def test_K26():
    app, req = build()
    ids = approve(app, req)
    for values in (['A' * 32], [ids[0][:-1]], ids * 2):
        check(app, req, values, 'schema', 'invalid_request')
    check(app, dict(asdict(req), unknown=1), ids, 'schema', 'invalid_request')


def test_K27():
    app, req = build()
    a = approve(app, req)
    b = approve(app, req)
    app._attestations._records[a[0]] = app._attestations._records[b[0]]
    check(app, req, a, 'integrity_failure')


def test_K28():
    app, req = build()
    ids = approve(app, req)
    old = app._attestations._records[ids[0]]
    app.revoke('qr', ids[0])
    app._attestations._records[ids[0]] = old
    check(app, req, ids, 'integrity_failure')


def test_K29():
    import hmac

    for variant in ('legacy', 'identity'):
        app, req = build()
        ids = approve(app, req)
        record, seal = app._attestations._records[ids[0]]
        if variant == 'identity':
            record = replace(record, registry_id='0' * 32)
        else:
            data = asdict(record)
            del data['registry_id']
            seal = hmac.new(
                app._attestations._key, json.dumps(data, sort_keys=True, default=str).encode(), hashlib.sha256
            ).hexdigest()
        app._attestations._records[ids[0]] = (record, seal)
        check(app, req, ids, 'integrity_failure')


def test_K30():
    app, req = build()
    ids = approve(app, req)
    app._verifier = 'wrong'
    check(app, req, ids, 'authorization_missing')


def test_K31(monkeypatch):
    app, req = build()
    b = app.prepare(req)
    ids = approve(app, req)
    with monkeypatch.context() as m:
        m.setattr(kp, 'canonical', Mock(side_effect=AssertionError('serialization before auth')))
        for token in ('bad', 'sa', 'ir', 'ap', None):
            with pytest.raises(PermissionError):
                app.inspect_bundle(token, req, b)
            with pytest.raises(PermissionError):
                app.inspect_attestation(token, ids[0])


def test_K32(monkeypatch, capsys):
    for target in ('inspect', 'encoding'):
        app, req = build()
        ids = approve(app, req)
        with monkeypatch.context() as m:
            if target == 'inspect':
                m.setattr(app._attestations, 'inspect', Mock(side_effect=RuntimeError('PRIVATE_SENTINEL')))
            else:
                m.setattr(kp, 'canonical', Mock(side_effect=RuntimeError('PRIVATE_SENTINEL')))
            check(app, req, ids, 'internal_failure')
    assert capsys.readouterr() == ('', '')


def test_K33():
    app, req = build()
    ids = approve(app, req)
    check(app, dict(asdict(req), exercise=True), ids, 'schema', 'invalid_request')
    app._requests = frozenset()
    check(app, req, ids, 'authorization_missing')


def test_K34():
    variants = [request(scope=s) for s in ('general', 'company', 'mixed')]
    variants += [
        request(question=q) for q in ('What is an RCP?', 'What is MORIQ policy?', 'MORIQ and code?', 'What is needed?')
    ]
    for other in variants:
        app, req = build(requests=(other,))
        check(app, other, approve(app, req), 'unsupported_scope')


def test_K35():
    app, req = build(tuple(f's-{i:02d}' for i in range(16)), k=16)
    ids = approve(app, req)
    assert len(ids) == 16
    check(app, req, ids)


def test_K36():
    app, req = build()
    for n in (17, 20):
        check(app, req, [None] * n, 'reference_limit', 'resource_limit')


def test_K37():
    from moriq.knowledge.citations import validate_references

    app, req = build()
    check(app, req, [None] * 21, 'reference_limit', 'resource_limit')
    assert validate_references(None, None, [None] * 21).status == 'resource_limit'


def test_K38():
    app, req = build()
    ids = approve(app, req)
    changes = [
        dict(question='x' * 513),
        dict(search_query='x' * 513),
        dict(jurisdiction='x' * 257),
        dict(edition='x' * 257),
        dict(search_query='x ' * 65),
        dict(search_query=' '.join('x' + str(i) for i in range(33))),
    ]
    for values in changes:
        check(app, replace(req, **values), ids, 'input_limit', 'resource_limit')
    envelope = replace(req, question='😀' * 512, search_query='😀' * 512, jurisdiction='😀' * 256, edition='😀' * 256)
    # Construct exactly 16,385 canonical bytes without exceeding individual field caps.
    excess = len(kp.canonical(asdict(envelope)).encode()) - 16385
    full, bmp, escaped = next(
        (a, b, c)
        for a in range(513)
        for b in range(11)
        for c in range(11)
        if 11 * a + 6 * b + 10 * c == excess and a + b + c <= 512
    )
    q = 'x' * full + '雪' * bmp + '\\' * escaped + '😀' * (512 - full - bmp - escaped)
    envelope = replace(envelope, question=q)
    assert len(kp.canonical(asdict(envelope)).encode()) == 16385
    check(app, envelope, ids, 'input_limit', 'resource_limit')
    for budget in ('documents', 'chunks', 'bytes'):
        app, req = build()
        c = app._registry.chunks()[0]
        if budget == 'documents':
            app._registry._chunks.update({str(i): (c,) for i in range(100)})
        elif budget == 'chunks':
            app._registry._chunks['s-a'] = (c,) * 10001
        else:
            app._registry._chunks['s-a'] = (replace(c, text='x' * 1200),) * 8333 + (replace(c, text='x' * 401),)
        check(app, req, ['0' * 32], 'corpus_limit', 'resource_limit')
    # Exactly 32,769 UTF-8 bytes in sixteen distinct 1,200-code-point chunks.
    pieces = []
    for i in range(16):
        prefix = f'stair width {i:02d} ' + ('😀' if i == 0 else '')
        chinese = 783 if i == 0 else 400
        pieces.append(prefix + '雪' * chinese + 'x' * (1200 - len(prefix) - chinese))
    body = ''.join(pieces)
    assert len(body.encode()) == 32769
    app, req = build(fixtures={'s-a': text_fixture(body)}, k=16)
    outcome(app.prepare(req), 'input_limit', 'resource_limit')
    # Independently size bounded metadata to make the bundle exactly 65,537 bytes.
    fixtures = {
        f's-{i:02d}': {
            'text': M['fixtures'][f's-{i:02d}']['text'],
            'metadata': dict(M['fixtures'][f's-{i:02d}']['metadata']),
        }
        for i in range(16)
    }
    app, req = build(tuple(fixtures), fixtures=fixtures, k=16)
    base = app.prepare(req)
    remaining = 65537 - len(kp.canonical(asdict(base)).encode())
    for fixture in fixtures.values():
        for name in ('title', 'publisher', 'author'):
            old = fixture['metadata'][name]
            extra = min(2048 - len(old), remaining)
            fixture['metadata'][name] += 'x' * extra
            remaining -= extra
    assert remaining == 0
    # Fingerprints remain fixed-width hex, so metadata growth is exact in canonical bytes.
    app, req = build(tuple(fixtures), fixtures=fixtures, k=16)
    outcome(app.prepare(req), 'input_limit', 'resource_limit')
    app, req = build()
    outcome(app.ingest('sa', 's-a', b'x' * 1000001), 'input_limit', 'resource_limit')


def test_K39():
    app, req = build()
    for value in (True, 0, 17):
        check(app, replace(req, max_hits=value), ['0' * 32], 'schema', 'invalid_request')
    for value in (None, [], 'request'):
        check(app, value, ['0' * 32], 'schema', 'invalid_request')
    for change in ({'scope': 'unknown'}, {'question': '\ud800'}, {'jurisdiction': 1}):
        check(app, replace(req, **change), ['0' * 32], 'schema', 'invalid_request')
    check(app, req, {}, 'schema', 'invalid_request')


def test_K40():
    app, req = build(())
    check(app, req, ['0' * 32], 'no_evidence')
    app, req = build(fixtures={'s-a': text_fixture('No matching body.')})
    check(app, req, ['0' * 32], 'no_evidence')


def test_K41():
    app, req = build()
    ids = approve(app, req)
    app.withdraw_source('ir', 's-a')
    check(app, req, ids, 'no_evidence')


def test_K42(monkeypatch):
    for source in (True, False):
        app, req = build()
        ids = approve(app, req)
        entered, resume, writing, done = (threading.Event() for _ in range(4))
        original = app._prepare

        def barrier(r):
            b = original(r)
            entered.set()
            assert resume.wait(3)
            return b

        monkeypatch.setattr(app, '_prepare', barrier)
        results = []
        reader = threading.Thread(target=lambda: results.append(app.check(req, ids)))

        def withdraw():
            writing.set()
            if source:
                app.withdraw_source('ir', 's-a')
            else:
                app.revoke('qr', ids[0])
            done.set()

        writer = threading.Thread(target=withdraw)
        reader.start()
        assert entered.wait(3)
        writer.start()
        assert writing.wait(3)
        assert not done.wait(0.05)
        resume.set()
        reader.join(3)
        writer.join(3)
        assert not reader.is_alive() and not writer.is_alive() and done.is_set()
        outcome(results[0])
        monkeypatch.setattr(app, '_prepare', original)
        check(app, req, ids, 'no_evidence' if source else 'stale_attestation')


def test_K43(monkeypatch):
    app, req = build()
    ids = approve(app, req)
    original = Gateway.eligible

    def epoch(*args):
        result = original(*args)
        app._registry._epoch += 1
        return result

    with monkeypatch.context() as m:
        m.setattr(Gateway, 'eligible', epoch)
        check(app, req, ids, 'stale_snapshot')
    original_inspect = app._inspect
    calls = 0

    def date_change(key):
        nonlocal calls
        result = original_inspect(key)
        calls += 1
        if calls == 2:
            FixedDate.current = (2026, 10, 17)
        return result

    monkeypatch.setattr(app, '_inspect', date_change)
    check(app, req, ids, 'clock_changed')


def test_K44():
    req = request(
        question='In the fictional Testland-A code exercise, what does the thermal bridge passage establish?',
        search_query='thermal bridge',
    )
    app, _ = build(requests=(req,), fixtures={'s-a': text_fixture(M['unicode_text'])})
    b = app.prepare(req)
    for e in b.entries:
        assert M['unicode_text'][e.start : e.end] == e.text
        assert e.chunk_sha256 == hashlib.sha256(e.text.encode()).hexdigest()
        assert e.chunk_id == independent_hash(
            dict(document_id=e.document_id, start=e.start, end=e.end, sha256=e.chunk_sha256)
        )
    check(app, req, approve(app, req))


def test_K45():
    a, req = build(('s-a', 's-b'))
    b, _ = build(('s-b', 's-a'))
    ai, bi = approve(a, req), approve(b, req)
    expected = a.prepare(req)
    for _ in range(100):
        assert a.prepare(req) == expected == b.prepare(req)
        assert check(a, req, ai) == check(b, req, list(reversed(bi)))


def test_K46():
    a, req = build()
    ids = approve(a, req)
    b, _ = build()
    check(b, req, ids, 'missing_applicability')


def test_K47():
    assert citations_valid(Draft('All stairs are compliant [1].', ('1',)), {'1'})
    app, req = build()
    result = check(app, req, approve(app, req))
    assert not hasattr(result, 'draft') and not hasattr(result, 'answer')
    # Explicit v2 permission: invoke the original unchanged offline regression.
    from test_adversarial import AdversarialTests

    AdversarialTests(
        'test_false_claim_with_valid_id_is_not_a_public_answer'
    ).test_false_claim_with_valid_id_is_not_a_public_answer()


def test_K48():
    for text, ids in (('[99]', ('99',)), ('[01]', ('1',)), ('[1](x)', ('1',)), ('［1］', ('1',)), ('[1]', ('2',))):
        assert not citations_valid(Draft(text, ids), {'1'})


def test_K49():
    app, req = build()
    with pytest.raises(PermissionError):
        task3_attestation_adapter(registry=app._registry, source_id='s-a', question=req.question)


def test_K50(monkeypatch, capsys):
    import socket
    import subprocess
    import urllib.request

    from mock_harness import MockHarness

    app, req = build()
    ids = approve(app, req)
    forbidden = Mock(side_effect=AssertionError('Forbidden path'))
    for owner, name in (
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
        monkeypatch.setattr(owner, name, forbidden)
    check(app, req, ids)
    forbidden.assert_not_called()
    assert capsys.readouterr() == ('', '')
    tree = ast.parse(Path(kp.__file__).read_text())
    bad = {'respond', 'hold', 'public', 'view', '_run_worker', '_seal', '_load', '_current'}
    assert not any(
        isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in bad for n in ast.walk(tree)
    )


def test_K51(monkeypatch):
    app, req = build()
    ids = approve(app, req)
    entered, resume = threading.Event(), threading.Event()
    original = app._prepare

    def barrier(r):
        result = original(r)
        entered.set()
        assert resume.wait(3)
        return result

    monkeypatch.setattr(app, '_prepare', barrier)
    results = []
    thread = threading.Thread(target=lambda: results.append(app.check(req, ids)))
    thread.start()
    assert entered.wait(3)
    try:
        check(app, req, ids, 'busy', 'resource_limit')
    finally:
        resume.set()
        thread.join(3)
    assert not thread.is_alive()
    outcome(results[0])


def test_K52():
    app, req = build()
    ids = approve(app, req)
    app._calls = 1024
    check(app, req, ids, 'input_limit', 'resource_limit')
    assert app._calls == 1024
    app, req = build()
    app._proposals = 100
    outcome(
        app.propose_source('sa', SourceMetadata(**M['fixtures']['s-a']['metadata'])), 'input_limit', 'resource_limit'
    )
    app, req = build()
    b = app.prepare(req)
    app._records = 256
    outcome(
        app.propose_applicability('ap', req, b, '1', M['applicability'], FixedDate(2026, 10, 17)),
        'input_limit',
        'resource_limit',
    )


def test_frozen_manifest_and_independent_roles():
    assert [r['id'] for r in M['cases']] == [f'K{i:02d}' for i in range(1, 53)]
    altered = dict(CREDENTIALS)
    altered['qr'] = ('AP', 'QR')
    with pytest.raises(ValueError):
        kp.OfflineKnowledgePreflight(altered, request_hashes=[], source_hashes={})
    assert kp.Registry is __import__('moriq.knowledge.registry', fromlist=['Registry']).Registry
