"""Pinned synthetic fixture provisioning; gold labels never enter runtime calls."""

import datetime as dt
import hashlib
import json
from dataclasses import asdict, replace
from pathlib import Path

from moriq.knowledge.registry import Registry, SourceMetadata
from moriq.knowledge.retrieval import retrieve

RAW = Path(__file__).with_name('e46-v2.json').read_bytes()
assert hashlib.sha256(RAW).hexdigest() == '4be7da6705b917b58a74230b374abb032444c4901816f5b447c8f0b5957ac9b7'
SPEC = json.loads(RAW)
SOURCES = {s['source_id']: s for s in SPEC['sources']}
QUERIES = {q['query_id']: q for q in SPEC['queries']}
CREDS = {
    'author': ('E46-test-author', {'author'}),
    'reviewer': ('E46-test-reviewer', {'reviewer'}),
    'self-reviewer': ('E46-test-author', {'reviewer'}),
}
REAL_DATE, REAL_TIME = dt.date, dt.datetime


class Time(REAL_TIME):
    current = (2026, 10, 20, 12, 0, 0)

    @classmethod
    def now(cls, tz=None):
        return cls(*cls.current, tzinfo=tz)


class Date(REAL_DATE):
    @classmethod
    def today(cls):
        return cls(*Time.current[:3])


def empty():
    return Registry(CREDS, local_references=[s['metadata']['reference'] for s in SOURCES.values()])


def populate(ids):
    registry = empty()
    for key in ids:
        s = SOURCES[key]
        m = SourceMetadata(**s['metadata'])
        record = registry.propose('author', m)
        assert record.document_id == s['document_id']
        if s['setup_state'] == 'pending':
            continue
        registry.approve('reviewer', key, record.document_id)
        chunks = registry.ingest('author', key, s['utf8_text'].encode('utf-8'))
        assert len(chunks) == len(s['passages'])
        for c, p in zip(chunks, s['passages'], strict=True):
            assert all(
                getattr(c, field) == p[field] for field in ('chunk_id', 'document_id', 'start', 'end', 'content_sha256')
            )
        if s['setup_state'] != 'active':
            registry.withdraw('reviewer', key, state=s['setup_state'])
    return registry


def corpus(count, size=None, *, citation=False):
    registry = empty()
    for i in range(count):
        text = f'TEST_ONLY synthetic thermal bridge token {i:03d}. '
        if citation:
            text = f'alpha token{i:02d}'
        if size is not None:
            n = size(i) if callable(size) else size
            text = (text * (n // len(text) + 1))[:n]
        key = f'e46-size-{i:03d}'
        m = replace(
            SourceMetadata(**SOURCES['eval46-s01']['metadata']),
            source_id=key,
            reference=f'https://fixtures.invalid/{key}',
            content_sha256=hashlib.sha256(text.encode()).hexdigest(),
        )
        p = registry.propose('author', m)
        registry.approve('reviewer', key, p.document_id)
        registry.ingest('author', key, text.encode())
    return registry


def run_query(q, registry=None):
    if registry is None:
        registry = populate(q['corpus_source_ids'])
    return registry, retrieve(q['text'], registry, **q['request'])


def observed(result):
    data = asdict(result)
    for hit in data['hits']:
        hit['chunk']['provenance'].pop('reviewed_at')
    return data


def assert_query(q, result):
    assert (result.status, result.reason) == (q['expected_status'], q['expected_reason'])
    ids = [f'{h.chunk.source_id}:p{h.chunk.start // 1200:03d}' for h in result.hits]
    assert ids == q['expected_ordered_passage_ids']
    assert result.claim_status == 'not_assessed' and result.release_allowed is False
    assert len(ids) == len(set(ids))
    for hit in result.hits:
        s = SOURCES[hit.chunk.source_id]
        p = next(p for p in s['passages'] if p['chunk_id'] == hit.chunk.chunk_id)
        assert all(getattr(hit.chunk, k) == p[k] for k in ('start', 'end', 'document_id', 'content_sha256'))
        assert hit.chunk.text == s['utf8_text'][p['start'] : p['end']]
        assert hit.chunk.provenance.lifecycle == 'active'
    return ids


def refs(result):
    return [{k: getattr(h.chunk, k) for k in ('source_id', 'document_id', 'chunk_id')} for h in result.hits]
