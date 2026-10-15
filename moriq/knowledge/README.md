# Task 4 — Offline architectural knowledge prototype

This directory is an isolated **review-only** experiment, not a live MORIQ AI
knowledge system or a replacement for Task 3's source gate. Nothing here
registers with Open WebUI or calls Ollama, an external API, or a vector store.

## First milestone

- Store explicit source ID, title, HTTPS provenance URL, exact excerpt,
  public/reviewed flags, review date, optional jurisdiction and edition.
- Return deterministic keyword-overlap matches with stable ordering.
- Exclude sources not explicitly marked both public and reviewed.
- Restrict jurisdiction-scoped search to sources with an exact match.
- Return source-linked passages only: **not certified claims or public answers**.
- No private/internal MORIQ ingestion; example.org appears in tests only and is
  synthetic, **not a genuinely verified architectural source**.

## Review and safety limitations

The `reviewed` flag is **untrusted caller-supplied data**: it proves nothing
about provenance, licensing, authoritativeness, freshness or applicability.
This module has **no authenticated approval or attestation binding**.
Do not feed arbitrary uploads into it and call the result verified.

Source URL syntax checking is not URL ownership verification, and retrieval
scores are lexical overlap rather than semantic evidence validation. Excerpts
might be out of context or adversarial. Querying a code-related subject
without exact jurisdiction/edition validation cannot establish code compliance.
There is no automatic answer generation, citation-to-claim audit, streaming,
document parser, database, index lifecycle, or deployed integration.

## Run the isolated tests

From `moriq/knowledge`:

```shell
python -m pytest -q test_retrieval.py
```

Task 4.1 status: 9 local isolated tests passed on 2026-10-14.
Tests have not yet been run in the Windows project environment or in CI.

## Required follow-up before real documents or a live adapter

1. Bind sources to independently authenticated Task 3 attestations and
   immutable content hashes; reject operator-supplied `reviewed=True` as
   an authority grant.
2. Define rights/licensing, public-source allowlisting, review expiry,
   source removal, edits, and edition/jurisdiction applicability.
3. Build a deterministic, bounded document extractor with injection-resistant
   metadata handling; freeze adversarial fixtures before implementation.
4. Build evaluation sets for no-evidence, mixed queries, wrong editions,
   misleading passages, citations and false-but-cited statements.
5. Integrate through a separately reviewed gate, with private drafts and
   no release of generated answers until claim-level review.
6. Review Task 3's unresolved production identity, audit storage, provenance,
   and cancellation/recovery gaps. **No live inference or deployment now.**

This is a safe scaffold; it does **not** satisfy Task 4 end-to-end.
