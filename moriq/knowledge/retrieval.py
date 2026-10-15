"""Deterministic, offline, review-only retrieval for public architecture sources.

No network, embeddings, model calls, or automatic answer publication.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Iterable

_TOKEN = re.compile(r"[a-z0-9]+", re.IGNORECASE)


@dataclass(frozen=True)
class Source:
    source_id: str
    title: str
    origin_url: str
    excerpt: str
    reviewed: bool
    public: bool
    reviewed_on: date | None = None
    jurisdiction: str | None = None
    edition: str | None = None

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,79}", self.source_id):
            raise ValueError("invalid source id")
        if not self.title.strip() or not self.excerpt.strip():
            raise ValueError("title and excerpt required")
        if not self.origin_url.startswith("https://"):
            raise ValueError("HTTPS provenance URL required")
        if self.reviewed and self.reviewed_on is None:
            raise ValueError("review date required for reviewed source")


@dataclass(frozen=True)
class Hit:
    source_id: str
    title: str
    excerpt: str
    origin_url: str
    score: int
    jurisdiction: str | None
    edition: str | None


def retrieve(
    question: str,
    sources: Iterable[Source],
    *,
    jurisdiction: str | None = None,
    max_hits: int = 5,
) -> tuple[Hit, ...]:
    """Return traceable excerpts; never call this an approved final answer.

    Sources must be independently approved, public, and date-stamped. The
    jurisdiction filter is exact: unscoped sources are not code authorities.
    """
    if not 1 <= max_hits <= 20:
        raise ValueError("max_hits must be between 1 and 20")
    terms = set(_TOKEN.findall(question.casefold()))
    if not terms:
        return ()
    hits: list[Hit] = []
    seen: set[str] = set()
    for source in sources:
        if source.source_id in seen:
            raise ValueError("duplicate source id")
        seen.add(source.source_id)
        if not (source.public and source.reviewed and source.reviewed_on):
            continue
        if jurisdiction is not None and source.jurisdiction != jurisdiction:
            continue
        body = set(_TOKEN.findall(source.excerpt.casefold()))
        heading = set(_TOKEN.findall(source.title.casefold()))
        score = len(terms & body) + 2 * len(terms & heading)
        if score:
            hits.append(
                Hit(source.source_id, source.title, source.excerpt,
                    source.origin_url, score, source.jurisdiction, source.edition)
            )
    hits.sort(key=lambda h: (-h.score, h.source_id))
    return tuple(hits[:max_hits])
