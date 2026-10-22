"""E46-v2 registry-only evaluation. Runtime receives no relevance labels."""

import ast
import builtins
import datetime as dt
import sys
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock

import pytest

import moriq.knowledge.registry as registry_module
from moriq.knowledge.citations import _references, validate_references
from moriq.knowledge.registry import SnapshotIntegrity, SourceMetadata, sha256, task3_attestation_adapter
from moriq.knowledge.retrieval import retrieve
from offline_evaluation.conftest import ENCODED, no_leak
from offline_evaluation.fixtures import (
    QUERIES,
    SOURCES,
    SPEC,
    Date,
    Time,
    assert_query,
    corpus,
    empty,
    observed,
    populate,
    refs,
    run_query,
)
from offline_evaluation.metrics import allocation, quantiles, ranking

CASES = [
    c
    for c in SPEC['cases']
    if c['case_id'].startswith(('Q', 'D'))
    or c['case_id']
    in {
        'E01',
        'E02',
        'E03',
        'E04',
        'E05',
        'E06',
        'E07',
        'E08',
        'E09',
        'E10',
        'E16',
        'E17',
        'E18',
        'E19',
        'E20',
        'E22',
        'E26',
    }
]


@pytest.fixture(autouse=True)
def fixed_clock(monkeypatch):
    Time.current = (2026, 10, 20, 12, 0, 0)
    monkeypatch.setattr(dt, 'date', Date)
    monkeypatch.setattr(dt, 'datetime', Time)


def state(result, status, reason):
    assert (result.status, result.reason) == (status, reason)
    assert result.claim_status == 'not_assessed' and result.release_allowed is False
    if status != 'passages':
        assert not getattr(result, 'hits', ())


def traced_integrity(call):
    tree = ast.parse(Path(registry_module.__file__).read_text())
    function = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == '_verify_document')
    sites = {
        n.lineno: i
        for i, n in enumerate(
            sorted((n for n in ast.walk(function) if isinstance(n, ast.Raise)), key=lambda n: n.lineno)
        )
    }
    events = []
    unexpected = []

    def trace(frame, event, arg):
        if event == 'exception' and frame.f_code.co_filename == registry_module.__file__:
            if arg[0] is SnapshotIntegrity:
                if frame.f_code.co_name == '_verify_document' and frame.f_lineno in sites:
                    events.append(sites[frame.f_lineno])
            elif arg[0] not in (StopIteration, GeneratorExit):
                unexpected.append(arg[0].__name__)
        return trace

    old = sys.gettrace()
    sys.settrace(trace)
    try:
        result = call()
    finally:
        sys.settrace(old)
    assert not unexpected
    return (result, events)


@pytest.mark.parametrize(
    'case,variant',
    [(c['case_id'], v) for c in CASES for v in c['variants']],
    ids=[c['case_id'] + '/' + v for c in CASES for v in c['variants']],
)
def test_frozen(case, variant, monkeypatch, record_property):
    record_property('case_id', case)
    record_property('variant_id', variant)
    if case in QUERIES:
        q = QUERIES[case]
        _, result = run_query(q)
        ids = assert_query(q, result)
        record_property('observed', observed(result))
        record_property('ranking', {str(k): ranking(q['relevant_passage_ids'], ids, k) for k in (1, 3, 5)})
        record_property('semantic_status', 'UNCOVERED' if q['stratum'] == 'diagnostic' else 'NOT_ASSESSED')
        return
    m = SourceMetadata(**SOURCES['eval46-s01']['metadata'])
    body = SOURCES['eval46-s01']['utf8_text'].encode()
    handlers = {
        'E01': evaluate_provenance,
        'E02': evaluate_approval,
        'E03': evaluate_rights,
        'E04': evaluate_modified_document,
        'E05': evaluate_citations,
        'E06': evaluate_citations,
        'E07': evaluate_citations,
        'E09': evaluate_citations,
        'E08': evaluate_citation_limit,
        'E10': evaluate_injection,
        'E16': evaluate_snapshot_integrity,
        'E17': evaluate_query_limits,
        'E18': evaluate_request_schema,
        'E19': evaluate_document_limit,
        'E20': evaluate_corpus_limit,
        'E22': evaluate_repeatability,
        'E26': evaluate_metric_oracles,
    }
    handlers[case](case, variant, monkeypatch, record_property, m, body)
    if case in {'E02', 'E03'} or (case == 'E04' and variant == 'body'):
        record_property('authorization_negative_attempts', 1)
        record_property('unauthorized_acceptances', 0)
    if case == 'E07':
        record_property('within_limit_invalid_citation_submissions', 1)
        record_property('invalid_citation_acceptances', 0)
    if case == 'E08' and variant != '20_valid':
        record_property('over_limit_citation_submissions', 1)


def test_registry_lane_isolation():
    assert not {'knowledge_preflight', 'private_draft_lifecycle', 'boundary', 'gateway'} & set(sys.modules)
    with pytest.raises(PermissionError, match='Task 3 adapter disabled'):
        task3_attestation_adapter(registry=empty(), source_id='eval46-s01', question='plan section')


def test_leakage_detector_oracles():
    for sample in ENCODED:
        with pytest.raises(AssertionError, match='Protected fixture output detected'):
            no_leak(sample)
    no_leak('E46_PRIVATE_CANARY')
    no_leak(b'{"status":"denied","release_allowed":false}')


def evaluate_provenance(case, variant, monkeypatch, record_property, m, body):
    r = populate(['eval46-s18', 'eval46-s19'])
    for sid in ('eval46-s18', 'eval46-s19'):
        assert ''.join(c.text for c in r.chunks() if c.source_id == sid).encode() == SOURCES[sid]['utf8_text'].encode()


def evaluate_approval(case, variant, monkeypatch, record_property, m, body):
    positive = populate(['eval46-s01'])
    assert retrieve('plan section', positive).status == 'passages'
    r = empty()
    if variant == 'no_author':
        with pytest.raises(PermissionError, match='^Not authorized\\.$'):
            r.propose('reviewer', m)
        assert not r._records
    else:
        p = r.propose('author', m)
        token = 'self-reviewer' if variant == 'self_review' else 'E46-forged-reviewer'
        if variant == 'self_review':
            assert r.inspect(token, m.source_id) == p
        with pytest.raises(
            PermissionError,
            match='^Independent reviewer required\\.$' if variant == 'self_review' else '^Not authorized\\.$',
        ):
            r.approve(token, m.source_id, p.document_id)
        assert r.inspect('reviewer', m.source_id) == p
    assert not r.chunks()


def evaluate_rights(case, variant, monkeypatch, record_property, m, body):
    assert populate([m.source_id]).chunks()
    field, value, message = {
        'license': ('license', 'unknown', 'Known license required.'),
        'usage': ('usage_permission', 'unknown', 'Explicit public redistribution permission required.'),
        'internal': ('classification', 'internal', 'Private or internal material prohibited.'),
    }[variant]
    r = empty()
    with pytest.raises(ValueError) as error:
        r.propose('author', replace(m, **{field: value}))
    assert str(error.value) == message and (not r._records)


def evaluate_modified_document(case, variant, monkeypatch, record_property, m, body):
    assert populate([m.source_id]).chunks()
    r = populate([m.source_id])
    if variant == 'body':
        with pytest.raises(ValueError, match='^Content changed; fresh review required\\.$'):
            r.ingest('author', m.source_id, body[:-1] + b'X')
        assert ''.join(c.text for c in r.chunks()).encode() == body
    else:
        p = r.propose('author', replace(m, title=m.title + ' revised'))
        assert p.lifecycle == 'pending' and p.review_status == 'pending' and (not r.chunks())


def evaluate_citations(case, variant, monkeypatch, record_property, m, body):
    r, result = run_query(QUERIES['Q01' if case == 'E05' else 'Q02'])
    selected = refs(result)[:1]
    state(validate_references(r, result, selected), 'references_valid', 'structural_only')
    if case == 'E05':
        r.withdraw('reviewer', m.source_id, state=variant)
        state(retrieve('plan section', r), 'evidence_gap', 'no_match')
        state(validate_references(r, result, selected), 'references_invalid', 'stale_or_mismatched')
    elif case == 'E07':
        change = {
            'fabricated_source': ('source_id', 'eval46-absent'),
            'fabricated_document': ('document_id', '0' * 64),
            'fabricated_chunk': ('chunk_id', '0' * 64),
            'wrong_pair': ('source_id', 'eval46-s06'),
        }
        if variant in change:
            k, v = change[variant]
            selected[0][k] = v
            assert _references(selected) is not None
            expected = 'unselected_or_stale'
        else:
            expected = 'invalid_schema'
            if variant == 'extra_key':
                selected[0]['reviewed'] = True
            elif variant == 'missing_key':
                del selected[0]['document_id']
            elif variant == 'duplicate':
                selected.append(dict(selected[0]))
            else:
                selected = []
        state(validate_references(r, result, selected), 'references_invalid', expected)
    elif case == 'E09':
        assert 'violet' not in SOURCES['eval46-s02']['utf8_text'].split()
        record_property('semantic_status', 'UNCOVERED')


def evaluate_citation_limit(case, variant, monkeypatch, record_property, m, body):
    r = corpus(20, citation=True)
    result = retrieve('alpha', r, max_hits=20)
    selected = refs(result)
    assert len(selected) == 20
    state(validate_references(r, result, selected), 'references_valid', 'structural_only')
    if variant != '20_valid':
        selected.append(dict(selected[0]))
        if variant == '21_invalid_ids':
            selected = [{'source_id': '!'}] * 21
        if variant == '21_invalid_context':
            r, result = (None, None)
        state(validate_references(r, result, selected), 'resource_limit', 'reference_limit')


def evaluate_injection(case, variant, monkeypatch, record_property, m, body):
    r = populate(['eval46-s20'])
    with monkeypatch.context() as mp:
        traps = [Mock(side_effect=AssertionError('Source text execution')) for _ in range(2)]
        mp.setattr(builtins, 'exec', traps[0])
        mp.setattr(builtins, 'eval', traps[1])
        result = retrieve('thermal bridge', r)
        assert all(t.call_count == 0 for t in traps)
    state(result, 'passages', 'review_required')
    assert result.hits[0].chunk.text == SOURCES['eval46-s20']['utf8_text']
    with pytest.raises(PermissionError, match='Task 3 adapter disabled'):
        task3_attestation_adapter(registry=r, source_id='eval46-s20', question='thermal bridge')


def evaluate_snapshot_integrity(case, variant, monkeypatch, record_property, m, body):
    positive = populate([m.source_id])
    normal = retrieve('plan section', positive)
    watched, events = traced_integrity(lambda: retrieve('plan section', positive))
    assert normal == watched and (not events)
    assert_query(QUERIES['Q01'], normal)
    r = populate([m.source_id])
    key = m.source_id
    if variant == 'metadata':
        r._records[key] = replace(r._records[key], metadata=replace(m, title=m.title + ' altered'))
    elif variant in ('chunk_hash', 'offset'):
        c = r._chunks[key][0]
        r._chunks[key] = (
            replace(c, **{'content_sha256': '0' * 64} if variant == 'chunk_hash' else {'end': c.end + 1}),
        )
    else:
        original = r.snapshot

        def intervening():
            value = original()
            r.propose('author', SourceMetadata(**SOURCES['eval46-s02']['metadata']))
            return value

        monkeypatch.setattr(r, 'snapshot', intervening)
    result, events = traced_integrity(lambda: retrieve('plan section', r))
    if variant != 'epoch':
        assert events == [{'metadata': 1, 'chunk_hash': 3, 'offset': 2}[variant]]
    else:
        assert not events and r._epoch > positive._epoch
    record_property('integrity_guard', events)
    state(
        result,
        'evidence_gap' if variant == 'epoch' else 'integrity_error',
        'stale_snapshot' if variant == 'epoch' else 'integrity_error',
    )


def evaluate_query_limits(case, variant, monkeypatch, record_property, m, body):
    value = {
        'chars512': 'x' * 512,
        'chars513': 'x' * 513,
        'raw64': ' '.join(['x'] * 64),
        'raw65': ' '.join(['x'] * 65),
        'unique32': ' '.join(f'q{i}' for i in range(32)),
        'unique33': ' '.join(f'q{i}' for i in range(33)),
    }[variant]
    limit = variant in ('chars513', 'raw65', 'unique33')
    state(
        retrieve(value, empty()), 'resource_limit' if limit else 'evidence_gap', 'query_limit' if limit else 'no_match'
    )


def evaluate_request_schema(case, variant, monkeypatch, record_property, m, body):
    r = populate([m.source_id])
    assert_query(QUERIES['Q01'], retrieve('plan section', r))
    options = {
        'k1': {'max_hits': 1},
        'k20': {'max_hits': 20},
        'k0': {'max_hits': 0},
        'k21': {'max_hits': 21},
        'kbool': {'max_hits': True},
        'question_none': {'question': None},
        'bad_scope': {'scope': 'unsupported'},
    }[variant]
    args = dict(question='plan section', registry=r)
    args.update(options)
    result = retrieve(**args)
    state(
        result,
        'passages' if variant in ('k1', 'k20') else 'invalid_request',
        'review_required' if variant in ('k1', 'k20') else 'invalid_request',
    )
    if result.hits:
        assert result.hits[0].chunk.source_id == m.source_id and len(result.hits) == 1


def evaluate_document_limit(case, variant, monkeypatch, record_property, m, body):
    assert sum(len(c.text.encode()) for c in corpus(1, 1000000).chunks()) == 1000000
    n = int(variant[5:])
    data = (b'alpha beta gamma ' * (n // 17 + 1))[:n]
    r = empty()
    p = r.propose('author', replace(m, content_sha256=sha256(data)))
    r.approve('reviewer', m.source_id, p.document_id)
    if n == 1000000:
        assert sum(len(c.text.encode()) for c in r.ingest('author', m.source_id, data)) == n
    else:
        with pytest.raises(ValueError, match='^Bounded document bytes required\\.$'):
            r.ingest('author', m.source_id, data)
        assert not r.chunks()


def evaluate_corpus_limit(case, variant, monkeypatch, record_property, m, body):
    positive = corpus(100, None if variant.startswith('docs') else 100000)
    state(retrieve('thermal bridge', positive), 'passages', 'review_required')
    r = (
        corpus(int(variant[4:]))
        if variant.startswith('docs')
        else corpus(100, lambda i: 100000 + int(i == 0 and variant == 'bytes10000001'))
    )
    limit = variant in ('docs101', 'bytes10000001')
    state(
        retrieve('thermal bridge', r),
        'resource_limit' if limit else 'passages',
        'corpus_limit' if limit else 'review_required',
    )


def evaluate_repeatability(case, variant, monkeypatch, record_property, m, body):
    comparisons = 0
    for q in QUERIES.values():
        order = list(q['corpus_source_ids'])
        if variant == 'reverse_insert':
            order.reverse()
        if variant == 'seed46_insert':
            order = q['repeatability_seed46_insertion_vector']
        shared = populate(order) if variant == 'same_instance' else None
        first = None
        for i in range(100):
            r = shared if shared is not None else populate(order)
            _, result = run_query(q, r)
            assert_query(q, result)
            data = observed(result)
            if i:
                assert data == first
                comparisons += 1
            else:
                first = data
    assert comparisons == 2772
    record_property('comparisons', comparisons)


def evaluate_metric_oracles(case, variant, monkeypatch, record_property, m, body):
    assert ranking(['A', 'B'], ['B', 'X', 'A'], 3) == dict(precision=2 / 3, recall=1, rr=1)
    assert ranking(['A'], [], 3) == dict(precision=0, recall=0, rr=0)
    assert ranking([], [], 3) == dict(precision=0, recall=None, rr=None)
    assert quantiles(list(range(1, 21))) == dict(n=20, p50=10.5, p95=19, max=20)
    assert allocation(100, 120, 150) == 50
    with pytest.raises(AssertionError):
        allocation(100, 50, 99)
