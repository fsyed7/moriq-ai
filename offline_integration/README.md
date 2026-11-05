# Task 6.1A offline request/status contracts

This module is an in-process contract exercise, not an authenticated HTTP service.
It has no generator, provider configuration, retrieval, ingestion or private view.
Only new files under offline_integration are required; no existing entrypoint imports it.

The trusted host provides two distinct object capabilities: boundary_key for
binding/revoking ActorContext objects after its own authentication, and executor_key
for advancing status. Client-created or copied contexts are rejected by object identity.
Neither capability belongs in an HTTP payload. This models trust placement; it does
not authenticate a person or provide protected durable audit.

Construct OfflineAdapter with the existing six independent synthetic lifecycle roles
and a bounded mapping from canonical RequestV1 hashes to exact tuples of SourceReference.
The mapping pins synthetic contract references, NOT source approval. It never grants
ingestion, applicability, citation validity or disclosure. No reference is resolved.
The adapter exclusively creates its own existing OfflinePrivateDraftLifecycle with an
empty source/fixture catalog. create_request performs existing request pin/role/clock/
audit checks. No alternate source approval or attestation authority is implemented.
The adapter adds only session ownership, cancellation and scheduling status. It exposes
no update of a registered question; a changed request needs a new ID and host pin.

RequestEnvelope contains version=1, request_id, session, existing RequestV1,
approved_source_references (tuple of source/document/chunk identities), and
generation='disabled'. It is paired with a host-issued ActorContext in start().
The misleading possibility in the field name is intentional to address integration
inputs: references are merely host-pinned offline inputs, not proof of current approval.
Dictionaries/JSON are rejected. A future HTTP decoder requires a separate contract.

start() returns a host-only Submission with a PublicResult and a random request-scoped
cancel_authority. Serialize ONLY public_json(), not dataclasses.asdict(Submission).
status() and cancel() require the same active context object. cancel() also requires
the exact per-request authority. It is not usable across actors, sessions or requests.
Public output never includes this secret, actor/session, prompt, source IDs or text.

The only progress is accepted(1) -> validating(2) -> failed(3), with code
'generation_disabled' for nonempty pinned refs or 'source_gap' for empty refs.
The trusted executor supplies the expected revision. No success answer, result body,
model response or arbitrary transition can be submitted. Cancellation from a nonterminal
state wins the lock and advances the revision to cancelled; repeated authorized cancel
is idempotent. Late executor ticks and terminal mutations reject without changing state.
Errors are operation errors, not mutations: unknown/unauthorized IDs have the same fixed
error/denied result with null request ID. All public sources arrays remain empty;
claim_status='not_assessed' and release_allowed=false always.

Limits: 16 active context objects, 32 accepted IDs (including terminal records, no eviction),
32 configured request hashes, 16 exact reference triples, 64-character safe identifiers,
512-code-point question/query, 256-code-point scope fields, 16 KiB canonical envelope.
Rejected start requests do not reserve their client IDs. Successful IDs cannot replay
in the owner's lifetime. Restart loses all state; old context/cancel capabilities do
not work in a new owner. No durable replay guarantee is claimed.

The existing lifecycle compares UTC date with host local date and poisons itself on
disagreement. Tests freeze both to 2026-11-02 noon UTC and separately prove disagreement
is denied. Real unfrozen time/identity/audit behavior needs a later reviewed design.
No existing clock safety checks were weakened.

## Tests

Use Python 3.12 and existing pytest. Put the repository and
moriq/brain/experimental/source_gate on PYTHONPATH; no production import-path change.
Run python -B -m pytest -q -p no:cacheprovider offline_integration/test_contracts.py.
Set PYTHONDONTWRITEBYTECODE=1 and disable unrelated pytest plugins. Frozen C01-C20
and five supplemental checks use synthetic fixtures and a fixed clock. Every case
asserts zero network/process/provider, registry access and private-view calls.
Tests of the existing fake HTTP transport run separately and require loopback access.

Production authentication, current source approval/applicability, protected audit,
real cancellation/idleness, private reviewer endpoints, and Studio connectivity are
not implemented. Do not expose adapter objects, host-only receipts, keys or internals
to untrusted Python code; Python object privacy is not a hostile-host sandbox.

## Task 6.1B offline backend facade

backend.py wraps the 6.1A adapter in an in-process byte/JSON facade. It has no listener and
is not an HTTP service. There is no separate decoder contract beyond this section and the tests.
Clients use handle(ticket, payload) with an out-of-band test ticket and the JSON operations
start, status and cancel. The host uses issue_session, revoke_session and tick; clients
cannot inject status changes or response bodies.

Limits: 32768 raw payload bytes, checked before JSON parsing, then the 6.1A limits above,
including the 16 KiB canonical envelope and 16 references. Duplicate keys and non-finite
JSON constants are rejected. Before accepting a request, and again on each nonterminal tick,
the facade checks pinned references against the synthetic registry through retrieval and
citation validation. This is a currency check, not answer release or claim review.

Known limitations: a job whose source is revoked stays non-terminal until cancelled, and
accepted IDs are not evicted before restart. test_B02_malformed's oversized payload is also
invalid JSON and returns the same invalid_request either way, so a pass does not prove the
size limit works. Run test_backend.py in its own process, as above. Frozen B01-B19 and the
task status are in docs/moriq-project/TASK-6.1B-CLOSEOUT.md; the owner accepted that record
for this offline facade only.
