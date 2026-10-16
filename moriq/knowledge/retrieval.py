"""Bounded lexical-v1 retrieval. Trusted offline passages, never answers."""

import re
from dataclasses import dataclass, field
from fractions import Fraction

from moriq.knowledge.registry import Chunk, Registry, SnapshotIntegrity, SnapshotLimit

_TOKEN = re.compile(r'[a-z0-9]+')
_STOP = frozenset(
    'a an the is are was were what how why does do can you me please explain describe to of in on for and'.split()
)


@dataclass(frozen=True)
class Request:
    question: str
    scope: str
    jurisdiction: str | None
    edition: str | None
    max_hits: int


@dataclass(frozen=True)
class Hit:
    chunk: Chunk
    phrase: int
    matched_terms: int
    body_tokens: int


@dataclass(frozen=True)
class RetrievalResult:
    status: str
    reason: str
    hits: tuple[Hit, ...] = ()
    context: Request | None = None
    claim_status: str = field(default='not_assessed', init=False)
    release_allowed: bool = field(default=False, init=False)


def in_scope(chunk, request):
    meta = chunk.provenance.metadata
    kinds = {'code'} if request.scope == 'code' else {'educational', 'guidance'}
    return (
        meta.source_type in kinds
        and (request.jurisdiction is None or meta.jurisdiction == request.jurisdiction)
        and (request.edition is None or meta.code_edition == request.edition)
    )


def _rank(chunks, request, phrase):
    terms = set(phrase)
    hits = []
    for chunk in chunks:
        if not in_scope(chunk, request):
            continue
        body = _TOKEN.findall(chunk.text.casefold())
        if not terms <= set(body):
            continue
        exact = int(
            len(phrase) >= 2 and any(body[i : i + len(phrase)] == phrase for i in range(len(body) - len(phrase) + 1))
        )
        hits.append(Hit(chunk, exact, len(terms), len(body)))
    hits.sort(
        key=lambda h: (
            -h.phrase,
            -Fraction(h.matched_terms, h.body_tokens),
            h.chunk.source_id,
            h.chunk.document_id,
            h.chunk.start,
            h.chunk.chunk_id,
        )
    )
    selected, seen = [], set()
    for hit in hits:
        c = hit.chunk
        m = c.provenance.metadata
        key = (m.source_type, m.jurisdiction, m.code_edition, c.content_sha256, c.text)
        if key not in seen:
            seen.add(key)
            selected.append(hit)
            if len(selected) == request.max_hits:
                break
    return tuple(selected)


def _query(request):
    if (
        type(request.question) is not str
        or type(request.max_hits) is not int
        or not 1 <= request.max_hits <= 20
        or type(request.scope) is not str
        or request.scope not in {'general', 'code', 'company', 'mixed'}
        or any(v is not None and type(v) is not str for v in (request.jurisdiction, request.edition))
    ):
        return 'invalid_request', 'invalid_request', []
    if len(request.question) > 512:
        return 'resource_limit', 'query_limit', []
    raw = _TOKEN.findall(request.question.casefold())
    phrase = [t for t in raw if t not in _STOP]
    if len(raw) > 64 or len(set(phrase)) > 32:
        return 'resource_limit', 'query_limit', []
    if (
        request.scope in {'company', 'mixed'}
        or {'moriq', 'company', 'internal'} & set(raw)
        or any(raw[i : i + 2] in [['our', 'firm'], ['office', 'policy']] for i in range(len(raw) - 1))
    ):
        return 'evidence_gap', 'unsupported_scope', []
    if request.scope == 'code' and not all(v and v.strip() for v in (request.jurisdiction, request.edition)):
        return 'evidence_gap', 'missing_scope', []
    if any(v is not None and not v.strip() for v in (request.jurisdiction, request.edition)):
        return 'invalid_request', 'invalid_request', []
    if not phrase:
        return 'evidence_gap', 'empty_query', []
    return '', '', phrase


def retrieve(question, registry, *, scope='general', jurisdiction=None, edition=None, max_hits=5):
    request = Request(question, scope, jurisdiction, edition, max_hits)
    if type(registry) is not Registry:
        return RetrievalResult('invalid_request', 'registry_required')
    status, reason, phrase = _query(request)
    if status:
        return RetrievalResult(status, reason)
    try:
        epoch, chunks = registry.snapshot()
    except SnapshotLimit:
        return RetrievalResult('resource_limit', 'corpus_limit')
    except SnapshotIntegrity:
        return RetrievalResult('integrity_error', 'integrity_error')
    hits = _rank(chunks, request, phrase)
    if not registry.current(epoch):
        return RetrievalResult('evidence_gap', 'stale_snapshot')
    if not hits:
        return RetrievalResult('evidence_gap', 'no_match')
    return RetrievalResult('passages', 'review_required', hits, request)
