"""Frozen Task 4.3 cases: synthetic only; no live providers."""

import importlib
import json
from dataclasses import replace
from pathlib import Path

import pytest

from moriq.knowledge.registry import Registry, SourceMetadata, task3_attestation_adapter
from moriq.knowledge.retrieval import retrieve

MANIFEST = json.loads((Path(__file__).parent / 'evaluation/task43-v1.json').read_text())


def build(*keys):
    r = Registry({'a': ('author', {'author'}), 'r': ('reviewer', {'reviewer'})})
    for key in keys:
        f = MANIFEST['fixtures'][key]
        record = r.propose('a', SourceMetadata(**f['metadata']))
        assert record.document_id == f['document_id']
        r.approve('r', key, record.document_id)
        chunks = r.ingest('a', key, f['text'].encode())
        assert chunks[0].chunk_id == f['chunk_id']
    return r


def search(r, query='thermal bridge', **kw):
    result = retrieve(query, r, **kw)
    assert result.claim_status == 'not_assessed'
    assert result.release_allowed is False
    if result.status != 'passages':
        assert result.hits == ()
    return result


def ids(result):
    return [h.chunk.source_id for h in result.hits]


def ref(key):
    f = MANIFEST['fixtures'][key]
    return {'source_id': key, 'document_id': f['document_id'], 'chunk_id': f['chunk_id']}


def validate(r, result, refs):
    v = importlib.import_module('moriq.knowledge.citations').validate_references(r, result, refs)
    assert v.claim_status == 'not_assessed' and v.release_allowed is False
    if v.status != 'references_valid':
        assert v.references == ()
    return v.status


def code(r, **kw):
    options = dict(scope='code', jurisdiction='Testland-A', edition='E1')
    options.update(kw)
    return search(r, 'stair width', **options)


def test_R01():
    assert ids(search(build('edu-a', 'edu-i'))) == ['edu-a']


def test_R02():
    assert search(build()).status == 'evidence_gap'


def test_R03():
    assert search(build('edu-i')).status == 'evidence_gap'


def test_R04():
    assert search(build('edu-d')).status == 'evidence_gap'


def test_R05():
    assert ids(search(build('edu-a', 'edu-b'))) == ['edu-a', 'edu-b']


def test_R06():
    assert search(build('edu-a'), 'thermal bridge insulation').status == 'evidence_gap'


def test_R07():
    assert ids(search(build('edu-a', 'edu-c'))) == ['edu-a', 'edu-c']


def test_R08():
    assert ids(search(build('edu-a', 'edu-k'))) == ['edu-a', 'edu-k']


def test_R09():
    assert ids(search(build('edu-a', 'edu-e'))) == ['edu-a']


def test_R10():
    r = build('edu-a', 'edu-e')
    old = search(r)
    r.withdraw('r', 'edu-a')
    assert ids(search(r)) == ['edu-e']
    assert validate(r, old, [ref('edu-a')]) == 'references_invalid'


def test_R11():
    assert ids(code(build('code-a', 'code-b', 'code-c', 'edu-j'))) == ['code-a']


def test_R12():
    assert code(build('code-c')).status == 'evidence_gap'


def test_R13():
    assert code(build('code-b')).status == 'evidence_gap'


def test_R14():
    for field in ['jurisdiction', 'edition']:
        assert code(build('code-a'), **{field: None}).reason == 'missing_scope'


def test_R15():
    assert code(build('code-a'), jurisdiction='testland-a').status == 'evidence_gap'


def test_R16():
    for state in ['revoked', 'retired', 'superseded']:
        r = build('edu-a')
        old = search(r)
        r.withdraw('r', 'edu-a', state=state)
        assert search(r).status == 'evidence_gap'
        assert validate(r, old, [ref('edu-a')]) == 'references_invalid'


def test_R17():
    r = build()
    m = MANIFEST['fixtures']['edu-a']['metadata']
    r.propose('a', SourceMetadata(**m))
    assert search(r).status == 'evidence_gap'
    with pytest.raises(TypeError):
        SourceMetadata(**m, reviewed=True)


def test_R18():
    r = build('edu-a')
    original = r.chunks()
    with pytest.raises(ValueError):
        r.ingest('a', 'edu-a', (MANIFEST['fixtures']['edu-a']['text'] + '!').encode())
    assert r.chunks() == original
    assert ids(search(r)) == ['edu-a']


def test_R19():
    r = build('edu-a')
    old = search(r)
    r.propose('a', replace(r.inspect('r', 'edu-a').metadata, revision='2'))
    assert search(r).status == 'evidence_gap'
    assert validate(r, old, [ref('edu-a')]) == 'references_invalid'


def test_R20():
    r = build('edu-a')
    r._chunks['edu-a'] = (replace(r.chunks()[0], content_sha256='0' * 64),)
    assert search(r).status == 'integrity_error'


def test_R21():
    for change in ['missing', 'offset', 'document']:
        r = build('edu-a')
        if change == 'missing':
            r._chunks['edu-a'] = ()
        elif change == 'offset':
            r._chunks['edu-a'] = (replace(r.chunks()[0], start=1),)
        else:
            r._records['edu-a'] = replace(
                r._records['edu-a'], metadata=replace(r._records['edu-a'].metadata, content_sha256='0' * 64)
            )
        assert search(r).status == 'integrity_error'


def test_R22(monkeypatch):
    import socket
    import subprocess
    import urllib.request

    r = build('edu-h')
    before = r.inspect('r', 'edu-h')

    def forbidden(*args, **kwargs):
        pytest.fail('External action attempted')

    monkeypatch.setattr(socket, 'socket', forbidden)
    monkeypatch.setattr(subprocess, 'Popen', forbidden)
    monkeypatch.setattr(urllib.request, 'urlopen', forbidden)
    for method in ['approve', 'propose', 'withdraw', 'ingest']:
        monkeypatch.setattr(r, method, forbidden)
    result = search(r)
    assert result.hits[0].chunk.text == MANIFEST['fixtures']['edu-h']['text']
    assert r.inspect('r', 'edu-h') == before


def test_R23():
    assert ids(search(build('edu-f', 'edu-g'), 'synthetic ventilation')) == ['edu-f', 'edu-g']


def test_R24():
    for scope in ['company', 'mixed']:
        assert search(build('edu-a', 'edu-h'), scope=scope).reason == 'unsupported_scope'


def test_R25():
    assert search(build('edu-a', 'edu-h'), 'MORIQ thermal bridge').reason == 'unsupported_scope'


def test_R26():
    for q in ['', '?!', 'what is the']:
        assert search(build('edu-a'), q).reason == 'empty_query'


def test_R27():
    for keys, q in [
        (('edu-a', 'edu-i'), 'thermal bridge'),
        (('edu-a', 'edu-b'), 'thermal bridge'),
        (('edu-a', 'edu-e'), 'thermal bridge'),
        (('edu-f', 'edu-g'), 'synthetic ventilation'),
    ]:
        r, reverse = build(*keys), build(*reversed(keys))

        def signature(result):
            return [(h.chunk.chunk_id, h.phrase, h.matched_terms, h.body_tokens) for h in result.hits]

        expected = signature(search(r, q))
        for _ in range(100):
            assert signature(search(r, q)) == expected == signature(search(reverse, q))


def test_R28():
    r = build('edu-a', 'edu-b', 'edu-c', 'edu-k')
    full = ids(search(r))
    for k in [1, 2]:
        assert ids(search(r, max_hits=k)) == full[:k]


def test_R29():
    r = build('edu-a')
    for value in [0, 21, True, '5']:
        assert search(r, max_hits=value).status == 'invalid_request'
    for kw in [{'scope': 'unknown'}, {'jurisdiction': 2}, {'edition': []}]:
        assert search(r, **kw).status == 'invalid_request'
    assert search(r, None).status == 'invalid_request'


def test_R30():
    assert search(build('edu-a'), 'thermal bridge not').status == 'evidence_gap'


def test_C01():
    r = build('edu-a', 'edu-i')
    assert validate(r, search(r), [ref('edu-a')]) == 'references_valid'


def test_C02():
    r = build('edu-a', 'edu-e')
    assert validate(r, search(r), [dict(ref('edu-a'), source_id='edu-e')]) == 'references_invalid'


def test_C03():
    r = build('edu-a', 'edu-i')
    assert validate(r, search(r), [dict(ref('edu-a'), chunk_id=ref('edu-i')['chunk_id'])]) == 'references_invalid'


def test_C04():
    r = build('edu-a', 'edu-i')
    assert validate(r, search(r), [ref('edu-i')]) == 'references_invalid'


def test_C05():
    r = build('edu-a', 'edu-e')
    assert validate(r, search(r), [ref('edu-e')]) == 'references_invalid'


def test_C06():
    r = build('edu-a')
    good = ref('edu-a')
    changes = [
        {'chunk_id': good['chunk_id'].upper()},
        {'chunk_id': good['chunk_id'][:8]},
        {'source_id': ' edu-a'},
        {'source_id': 'ｅdu-a'},
        {'source_id': 'fabricated'},
        {'chunk_id': '0' * 64},
        {'source_id': 1},
    ]
    for change in changes:
        assert validate(r, search(r), [dict(good, **change)]) == 'references_invalid'
    for refs in [[], [good, good]]:
        assert validate(r, search(r), refs) == 'references_invalid'


def test_C07():
    for operation in ['withdraw', 'propose']:
        r = build('edu-a')
        result = search(r)
        if operation == 'withdraw':
            r.withdraw('r', 'edu-a')
        else:
            r.propose('a', r.inspect('r', 'edu-a').metadata)
        assert validate(r, result, [ref('edu-a')]) == 'references_invalid'


def test_C08():
    r = build('edu-a')
    for key in ['reviewed', 'url', 'text', 'approval']:
        assert validate(r, search(r), [dict(ref('edu-a'), **{key: True})]) == 'references_invalid'


def test_C09():
    r = build('edu-a')
    result = search(r)
    for change in [{'text': 'altered'}, {'start': 1}, {'content_sha256': '0' * 64}]:
        hit = replace(result.hits[0], chunk=replace(result.hits[0].chunk, **change))
        assert validate(r, replace(result, hits=(hit,)), [ref('edu-a')]) == 'references_invalid'


def test_C10():
    r = build('edu-a')
    incorrect_claim = 'A thermal bridge prevents all heat transfer.'
    result = search(r)
    assert validate(r, result, [ref('edu-a')]) == 'references_valid'
    assert result.claim_status == 'not_assessed' and result.release_allowed is False
    assert incorrect_claim not in repr(result)
    assert not hasattr(result, 'answer')


def test_C11():
    r = build('code-a', 'code-c', 'edu-a')
    for result in [search(r), code(r, edition='E2')]:
        assert validate(r, result, [ref('code-a')]) == 'references_invalid'


def test_L01(monkeypatch):
    module = importlib.import_module('moriq.knowledge.retrieval')
    original = module._rank
    r = build('edu-a')

    def withdraw_at_barrier(*args):
        result = original(*args)
        r.withdraw('r', 'edu-a')
        return result

    monkeypatch.setattr(module, '_rank', withdraw_at_barrier)
    result = search(r)
    assert result.status == 'evidence_gap' and result.reason == 'stale_snapshot'


def test_L02():
    r = build('edu-a')
    for query in ['a' * 513, 'x ' * 65, ' '.join(f'x{i}' for i in range(33))]:
        assert search(r, query).status == 'resource_limit'
    assert validate(r, None, [None] * 21) == 'resource_limit'
    # These are preflight budget tests, not valid corpus fixtures; fail before integrity work.
    for budget in ['documents', 'chunks', 'bytes']:
        r = build('edu-a')
        original = r.chunks()[0]
        if budget == 'documents':
            for i in range(100):
                r._records[str(i)] = r._records['edu-a']
                r._chunks[str(i)] = (original,)
        elif budget == 'chunks':
            r._chunks['edu-a'] = (original,) * 10001
        else:
            # Bounded strings, <=1200 code points, sum just beyond 10 MB.
            item = replace(original, text='x' * 1200)
            r._chunks['edu-a'] = (item,) * 8333 + (replace(item, text='x' * 401),)
        assert search(r).status == 'resource_limit'


def test_L03():
    r = build('edu-a')
    with pytest.raises(PermissionError):
        task3_attestation_adapter(registry=r, source_id='edu-a', question='thermal bridge')


def test_reference_limit_precedes_every_element_check():
    r = build()
    for i in range(21):
        key = f'limit-{i:02d}'
        body = f'Thermal bridge fixture {i}.'
        import hashlib

        m = dict(
            MANIFEST['fixtures']['edu-a']['metadata'],
            source_id=key,
            content_sha256=hashlib.sha256(body.encode()).hexdigest(),
        )
        record = r.propose('a', SourceMetadata(**m))
        r.approve('r', key, record.document_id)
        r.ingest('a', key, body.encode())
    result = search(r, max_hits=20)
    refs = [
        dict(source_id=h.chunk.source_id, document_id=h.chunk.document_id, chunk_id=h.chunk.chunk_id)
        for h in result.hits
    ]
    assert len(refs) == 20
    assert validate(r, result, refs) == 'references_valid'
    assert validate(r, result, refs + [refs[0]]) == 'resource_limit'
    assert validate(r, None, [None] * 21) == 'resource_limit'
    assert validate(r, result, [dict(refs[0], chunk_id='0' * 64)]) == 'references_invalid'
    assert validate(r, result, []) == 'references_invalid'


def test_unicode_offsets_and_casefold():
    import hashlib

    r = build()
    text = MANIFEST['unicode_text']
    m = dict(MANIFEST['fixtures']['edu-a']['metadata'], content_sha256=hashlib.sha256(text.encode()).hexdigest())
    record = r.propose('a', SourceMetadata(**m))
    r.approve('r', 'edu-a', record.document_id)
    chunks = r.ingest('a', 'edu-a', text.encode())
    assert ''.join(c.text for c in chunks).encode() == text.encode()
    for c in chunks:
        assert text[c.start : c.end] == c.text
        assert hashlib.sha256(c.text.encode()).hexdigest() == c.content_sha256
        payload = {'document_id': record.document_id, 'start': c.start, 'end': c.end, 'sha256': c.content_sha256}
        expected = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        assert c.chunk_id == expected
    assert ids(search(r, 'THERMAL BRIDGE')) == ids(search(r, 'thermal bridge'))


def test_manifest_preserves_all_cases():
    assert [row['id'] for row in MANIFEST['cases']] == (
        [f'R{i:02d}' for i in range(1, 31)] + [f'C{i:02d}' for i in range(1, 12)] + [f'L{i:02d}' for i in range(1, 4)]
    )
