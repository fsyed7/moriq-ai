# Isolated synthetic knowledge preflight

Task 4.4A is an offline applicability preflight, with no draft generation or public
answer release. It is not a production integration. The original Task 4
`task3_attestation_adapter` remains disabled. No existing entry point imports this
module; run it only in the isolated source-gate harness with repository and
source-gate directories on the Python import path.

`OfflineKnowledgePreflight` owns one registry, one Task 3 offline attestation
instance, one coordinator lock and a single-flight check guard. Host configuration
pins synthetic source hashes, canonical request hashes and four independent
identities: source author (SA), ingestion reviewer (IR), applicability proposer
(AP), and question reviewer (QR). Tokens are test-only capabilities, not an identity
provider. No API accepts caller-supplied registry instances or retrieval results.

Source proposal, ingestion approval and ingestion are separate operations. A
`RequestV1` binds the exact question, separate search query, scope, jurisdiction,
edition and hit limit. `prepare` retrieves through the owned registry, validates
citations and creates a private `BundleV1`. Entries retain original source,
document and chunk IDs, Unicode text offsets, hashes and complete source records.
Aliases are assigned deterministically by source/document/offset/chunk order.
The bundle hash covers the full canonical JSON, including request and provenance.

AP proposes applicability for each selected entry against the current bundle.
QR independently approves it. The original Task 3 create/approve/inspect lifecycle
and integrity checks are reused; the adapter never signs records itself. Approval
binds the exact question, complete bundle, alias, passage and provenance. Ingestion
approval cannot satisfy question-specific approval. Each check rereads current
registry state and signed attestations, verifies all members and the pure Task 3
eligibility predicate, and rechecks epoch, records and date before returning.
Withdrawal and reviewer operations serialize on the same coordinator. Held
bundles are revalidated before creating or approving applicability records.

`check` returns only `Decision(status, reason, claim_status, release_allowed)`.
Statuses are `evidence_ready`, `evidence_gap`, `invalid_request`, and
`resource_limit`; reasons are fixed strings. Every result has
`claim_status='not_assessed'` and `release_allowed=False`. Readiness is a structural
observation at one instant, never a claim-verification result or release token.
Errors do not return passages, credentials, prompts or exception text. Operator
authorization failures raise a generic private `PermissionError`.

Limits: 16 selected entries/attestations (checked before individual reference
validation), 512-character question/query, 256-character jurisdiction/edition,
16 KiB canonical request, 32 KiB selected UTF-8 text, 64 KiB canonical bundle,
2,048-character applicability and at most seven days of applicability validity.
Task 4 query/corpus limits remain in force. A session admits at most 1,024 operator
calls, 100 source proposals and 256 applicability records; there is no reset or
eviction. Concurrent checks return `resource_limit/busy`. These are application
bounds, not OS quotas or hard latency guarantees. Task 4's separate citation
validator retains its existing 20-reference limit.

The generator callback is a fail-fast sentinel. No adapter path invokes generation,
`public`, `view`, workers, providers, sockets or subprocesses. K47 alone exercises
the unchanged historical mock false-claim regression, as authorized by the v2
specification clarification. K50 places runtime tripwires on forbidden APIs.
`knowledge_preflight-v1.json` preserves all 52 original acceptance rows verbatim,
specification hashes and synthetic fixtures. Tests include identity substitution,
revocation, replay, mutation, exact boundary limits, concurrent withdrawal and
Unicode offset checks. No dependencies were added.

Security assumptions: the host owns the process, configuration and Python object
graph; all authority-changing operations use this coordinator. Python attributes
are not a sandbox against malicious same-process code. Host compromise, clock
rollback, dishonest authorized reviewers, semantic conflicts and incorrect claims
with valid citations remain outside structural verification. Audit and authority
are bounded and process-local, with no durable identity, persistence or cross-process
transaction. Source text is always untrusted data. Future real-source, persistent,
worker or generated-draft integration requires separate review and authorization.

Publication remains gated by the implementation report. The unchanged historical
H15 hash assertion currently fails at the baseline; neither its evidence nor its
expected values are repaired by this change.
