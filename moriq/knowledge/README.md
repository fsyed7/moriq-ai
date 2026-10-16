# Task 4.2 — Offline knowledge foundation

This isolated module accepts approved UTF-8 text and Markdown bytes, builds
traceable chunks, and retrieves passages. It does not generate answers, grant
code authority, register with Open WebUI, or contact any service.

## Operator workflow

Run from the repository root with Python 3.11 or 3.12. A trusted host creates
`Registry(credentials, local_references=...)` with separate author and reviewer
identities. These are explicitly offline test credentials; configure them outside
uploaded metadata. No default identities or credentials are provided by the library.

1. The author constructs `SourceMetadata` and calls `propose(author_token, metadata)`.
   Required fields: stable source ID, title, HTTPS URL or approved opaque local
   reference, source type (`educational`, `guidance`, `code`), format (`text`,
   `markdown`), license, usage permission, public classification, exact original
   byte SHA-256, and revision. Publisher, author, publication date, jurisdiction
   and code edition can be unknown (`None`); code sources require jurisdiction
   and edition. Dates use YYYY-MM-DD. Unknown licenses and permissions are rejected.
2. A different reviewer calls `inspect(reviewer_token, source_id)` and independently
   verifies the exact original file and metadata: ownership/provenance, absence
   of private/internal material, actual permission for **public redistribution**,
   content hash, revision, and scope. `approve(reviewer_token, source_id, document_id)`
   binds that reviewed proposal. Metadata fields never authorize approval.
3. The author calls `ingest(author_token, source_id, original_bytes)`. Only an
   approved active record can be ingested. Strict UTF-8 decoding happens after
   hash verification. Input is bounded to 1,000,000 bytes. Empty, control-character
   binary, malformed UTF-8, mismatched hashes and unsupported formats are rejected.
   Rejected bodies are not persisted or logged. The registry itself opens no files.
4. `retrieve(question, registry, jurisdiction=..., edition=...)` ranks only currently
   ingested approved passages. Hits contain the entire chunk and immutable source
   provenance. Filters are exact matches; results are passages, never approved answers.
5. `withdraw(reviewer_token, source_id, state=...)` removes passages immediately;
   states are `revoked`, `retired`, or `superseded`. Reproposing any source ID
   increments its version, clears approval and removes old chunks. A new independent
   approval is required, even when bytes are identical. Old approval IDs cannot replay.

The Task 4.1 `Source(reviewed=True, ...)` API is intentionally removed. Its only
callers were the isolated tests. `retrieve` now requires a host-owned registry;
passing raw source lists or approval dictionaries fails closed.

## Determinism and provenance

The source ID is operator-assigned and stays stable across revisions. Document IDs
hash canonical metadata plus the registry version; approval timestamps do not affect
IDs. Chunk IDs hash document ID, start/end positions and the chunk content hash.
Repeated ingestion is idempotent. Equal metadata/version/bytes in fresh registries
produce equal IDs. A revision requires a different document/chunk identity.

Chunks are consecutive spans of at most 1,200 Unicode code points. Offsets are
zero-based, end-exclusive positions in the exact decoded source, **not UTF-8 byte
offsets**. UTF-8 BOM, CRLF, whitespace and Markdown syntax are preserved. Concatenated
chunks reconstruct the original bytes. No rendering, link fetching, normalization,
front-matter evaluation or document instructions are executed. Chunks may split a
paragraph or word; semantic parsing is outside this foundation.

Each chunk carries its source ID, document ID, source offsets, text hash and full
source record, including original byte hash, reviewer, UTC review timestamp, review
status and lifecycle. Source snapshots already returned to trusted callers cannot
be recalled; always query the registry afresh after changes. A failed attempt to
ingest modified bytes does not replace the previously approved original bytes.

## Trust boundary and Task 3

Task 3's source gate requires an independently reviewed exact question/content
binding, applicability, expiration, numeric citation IDs and registry-bound HMAC
records. Its public output is fixed status text; generated drafts stay in the
private reviewer boundary. Source-ingestion approval establishes none of those
question-level claims. `task3_attestation_adapter` always raises `PermissionError`;
there is no enable switch, live adapter, conversion to Task 3 reviews, or answer release.
Task 3 code, evidence files and tests are unchanged.

This registry reuses the independent-review and lifecycle pattern, not Task 3's
private signing key or mutable internals. It adds no signatures because it imports
no external approvals or stored records. All state is owned by one trusted process.
It is **not a hostile-Python sandbox, durable audit system or production identity
service**. Python code with access to the object or host configuration is trusted.
Do not expose registry objects, tokens, reviewer operations or raw exceptions to
untrusted clients. No public transport is implemented here.

Metadata syntax, hashes and review identities do not prove provenance, legal rights,
architectural correctness or confidentiality. An authorized reviewer can make a
mistake or mislabel private material; no automated privacy classifier is claimed.
Only synthetic fixtures were used; no real source body was ingested. A malicious
passage remains untrusted data even after ingestion review. Source approval has no
automatic expiration in this foundation; reviewers must withdraw stale sources.
Production authentication, protected persistent audit/lifecycle storage, qualified
source review and question-specific applicability remain gates before real use.

## Verification

From repository root:

```shell
python -m pytest -q moriq/knowledge
ruff check moriq/knowledge
ruff format --check moriq/knowledge
```

Tests cover deterministic Unicode/CRLF reconstruction, metadata/provenance rejection,
private/internal flags, licensing, roles and independent identities, stale content
and metadata approvals, lifecycle/replay, raw review-flag bypass, registry-only
retrieval, exact jurisdiction/edition filters and disabled Task 3 integration.

No database, embeddings, models, new dependencies, scraping, production deployment,
Docker, WebUI, paid service or Task 5 work is included.

## Task 4.3 — lexical-v1 and structured citations

Task 4.3 supersedes the retrieval return contract described above. `retrieve`
returns a `RetrievalResult` with `status`, fixed `reason`, `hits` and trusted
request `context`. Every result has `claim_status='not_assessed'` and
`release_allowed=False`. There is no answer field, generation callback or public
adapter. Non-passage results have no hits. Invalid inputs return fixed statuses.

Scope defaults to `general` (educational/guidance only). `scope='code'` requires
both exact jurisdiction and edition; missing scope is an evidence gap. Company
and mixed scope are unsupported; conservative company-query sentinels also gap.
No query routing or source review establishes company/code authority.

Matching uses Unicode casefolding followed by the specified ASCII `[a-z0-9]+`
tokenizer. Original Unicode text, CRLF and code-point offsets are unchanged;
there is no NFC/NFKC, stemming or multilingual-tokenizer promise. Every non-stop
query token must occur in the body. Titles cannot qualify a passage. Rank by
contiguous phrase, exact rational match density, then source/document/start/chunk
identity. Exact text duplicates within type/jurisdiction/edition share one
representative. Contradictory or merely similar text is not merged.

Each retrieval uses a locked, bounded integrity snapshot. It verifies original
byte hash, contiguous offsets, content hashes, existing document/chunk identity
algorithms and current approved/active provenance. No persistent index is built.
A monotonic process-local write counter detects intervening registry operations;
any write conservatively produces a stale-snapshot gap, including writes outside
the query scope. This can over-refuse but never reuses a stale ranking. Previously
returned bytes cannot be recalled. Host-private dictionary tampering is not a
supported update path or a security boundary against arbitrary Python execution.

Hard retrieval limits: 100 ingested documents, 10,000 chunks, 10,000,000 UTF-8
bytes; query 512 code points, 64 raw tokens, 32 retained distinct terms; k=1–20,
default 5. Corpus checks happen before flattening/hash/tokenization. The existing
per-document byte limit is unchanged. These bounds do not provide a hostile-user
quota for the underlying registry's number of pending proposals.

`validate_references(registry, result, references)` in `citations.py` accepts a
list/tuple of dictionaries containing exactly `source_id`, `document_id` and
`chunk_id`. Pass the original host-held retrieval result; never accept a result
or allowlist from an untrusted upload. It checks membership in selected hits,
current provenance, scope, offsets and hashes using a new integrity snapshot.

The citation status contract is exactly:

- `resource_limit`: more than 20 submitted references, checked BEFORE elements,
  registry or result context, even if entries are malformed. No truncation.
- `references_invalid`: within the count limit, but empty, malformed, duplicate,
  unselected, mismatched, stale, withdrawn or otherwise unresolvable references.
- `references_valid`: all submitted references resolve to current selected hits.

Within-limit registry resource/integrity failure produces `references_invalid`,
not `resource_limit`; only excessive submitted-reference count uses that status.
All failures return no validated references. Citation validity is structural,
never semantic entailment; even a valid citation on a false sentence cannot
release an answer. Task 3 remains entirely separate and its adapter disabled.

`evaluation/task43-v1.json` preserves all 44 scope-v1 rows verbatim, exact
synthetic fixtures and independently calculated IDs. It records the original
specification and authorized v2 clarification hashes. `test_citations.py` maps
one named test to each row, plus explicit 20/21 count precedence, Unicode/offset
and manifest regressions. Existing retrieval tests were migrated for explicit
results and no title weighting; safety assertions remain. No Task 3 files changed.

The 2026-10-16 specification correction only adds the third citation status and
count-first precedence. Original specification SHA-256:
`589e778966d3094ee12b8ac1fd44afc1ad854090921dedb5b2afd2d67e663e9a`.
Corrected specification (v1 bytes + LF + authorized addendum bytes) SHA-256:
`e4c8e7f0158873920c4a557f7910f4154c93a2befa44c38a21e6a885cbdd5df3`.

No real-source correctness, production identity, durable audit, automatic expiry,
semantic relevance or live inference is established by this synthetic checkpoint.
