"""Deterministic offline retrieval of registry-approved passages, not answers."""

import re
from dataclasses import dataclass

from moriq.knowledge.registry import Chunk, Registry

_TOKEN = re.compile(r'[a-z0-9]+', re.IGNORECASE)


@dataclass(frozen=True)
class Hit:
    chunk: Chunk
    score: int


def retrieve(
    question: str, registry: Registry, *, jurisdiction: str | None = None, edition: str | None = None, max_hits: int = 5
) -> tuple[Hit, ...]:
    """Only a trusted host registry supplies passages; uploaded review flags cannot."""
    if type(registry) is not Registry:
        raise ValueError('Trusted registry required; caller review flags are not authority.')
    if type(question) is not str or type(max_hits) is not int or not 1 <= max_hits <= 20:
        raise ValueError('Text query and max_hits between 1 and 20 required.')
    if any(value is not None and (type(value) is not str or not value.strip()) for value in (jurisdiction, edition)):
        raise ValueError('Invalid jurisdiction or edition filter.')
    terms = set(_TOKEN.findall(question.casefold()))
    hits = []
    for chunk in registry.chunks():
        source = chunk.provenance.metadata
        if jurisdiction is not None and source.jurisdiction != jurisdiction:
            continue
        if edition is not None and source.code_edition != edition:
            continue
        body = set(_TOKEN.findall(chunk.text.casefold()))
        heading = set(_TOKEN.findall(source.title.casefold()))
        score = len(terms & body) + 2 * len(terms & heading)
        if score:
            hits.append(Hit(chunk, score))
    hits.sort(key=lambda hit: (-hit.score, hit.chunk.source_id, hit.chunk.start))
    return tuple(hits[:max_hits])
