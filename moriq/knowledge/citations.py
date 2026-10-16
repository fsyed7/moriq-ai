"""Structured reference checks, never factual claim verification or answer release."""

import re
from dataclasses import dataclass, field

from moriq.knowledge.registry import Registry, SnapshotIntegrity, SnapshotLimit
from moriq.knowledge.retrieval import Request, RetrievalResult, _query, in_scope


@dataclass(frozen=True)
class CitationResult:
    status: str
    reason: str
    references: tuple[tuple[str, str, str], ...] = ()
    claim_status: str = field(default='not_assessed', init=False)
    release_allowed: bool = field(default=False, init=False)


def _references(refs):
    keys = []
    for ref in refs:
        if type(ref) is not dict or ref.keys() != {'source_id', 'document_id', 'chunk_id'}:
            return None
        key = (ref['source_id'], ref['document_id'], ref['chunk_id'])
        if (
            any(type(v) is not str for v in key)
            or re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:-]{0,79}', key[0]) is None
            or any(re.fullmatch(r'[0-9a-f]{64}', v) is None for v in key[1:])
        ):
            return None
        keys.append(key)
    return tuple(keys) if len(set(keys)) == len(keys) else None


def validate_references(registry, result, references):
    # Count precedes element, registry and context validation, including invalid IDs.
    if type(references) not in (list, tuple):
        return CitationResult('references_invalid', 'invalid_schema')
    if len(references) > 20:
        return CitationResult('resource_limit', 'reference_limit')
    keys = _references(references)
    if not keys:
        return CitationResult('references_invalid', 'invalid_schema')
    if (
        type(registry) is not Registry
        or type(result) is not RetrievalResult
        or result.status != 'passages'
        or type(result.context) is not Request
        or _query(result.context)[0]
        or not 1 <= len(result.hits) <= result.context.max_hits
    ):
        return CitationResult('references_invalid', 'invalid_context')
    try:
        epoch, chunks = registry.snapshot()
    except (SnapshotIntegrity, SnapshotLimit):
        return CitationResult('references_invalid', 'unavailable_registry')
    current = {(c.source_id, c.document_id, c.chunk_id): c for c in chunks}
    selected = {}
    for hit in result.hits:
        c = hit.chunk
        key = (c.source_id, c.document_id, c.chunk_id)
        if key in selected or current.get(key) != c or not in_scope(c, result.context):
            return CitationResult('references_invalid', 'stale_or_mismatched')
        selected[key] = c
    if any(key not in selected for key in keys) or not registry.current(epoch):
        return CitationResult('references_invalid', 'unselected_or_stale')
    return CitationResult('references_valid', 'structural_only', keys)
