# Task 3.5 — offline public/reviewer boundary and attestation lifecycle

October 14, 2026. Base: `9f487f08faef3fe09418b259232bbbabc8c39d04`,
branch `feature/brain-v0.2-experiments` (existing draft PR #12).
**Offline prototype implemented; NO-GO for live inference at this checkpoint.**
No production identity, model adapter, HTTP endpoint or deployment integration exists.

## Scope and public contract

`boundary.py` wraps the unchanged Task 3.4 `Gateway`. Only new prototype files
were added. Existing gateway callers/tests, prompt builders, experimental evidence,
deployment configuration, PR #11 and running applications were not changed.

The trusted host constructs `OfflinePrototype(test_credentials, mock_generator)`.
Only its `public(payload)` method is a public adapter. Its input is a JSON string
with `question` and optional `attestation_ids`; unknown/duplicate fields, uploaded
review metadata, invalid types and excessive request size are rejected. Public
callers cannot supply credentials, reviewers, documents, exercise mode or callbacks.

Every public response is a pre-serialized literal from a closed catalog:

```json
{"status": "review_required", "message": "Draft withheld for authorized review. No answer released."}
```

The schema has exactly `status` and `message`. It cannot carry `review_draft`,
gateway answer text, evidence, reviewer metadata, exception messages or model prose.
Unknown gateway statuses map to a fixed error. Normal exceptions are caught without
logging or serializing their content. Fixed response bytes also avoid a dynamic
public serialization failure path. Process termination and a hostile Python host
are outside this function-level guarantee.

Source-required questions without eligible evidence make zero generation calls.
The existing conservative education grammar still applies. Allowed general
education can generate a draft without company evidence, but that draft is private
too. No response-release feature was added. Citation validation is not fact checking.

## Separately authorized private interface

- `create(token, ...)` requires the author role and creates a pending proposal.
- `inspect(token, id)` requires the reviewer role and returns the exact immutable
  proposal for independent assessment before approval.
- `approve`, `revoke`, `supersede`, `view` and `audit` require the reviewer role.
- `view(token)` returns private JSON drafts only after checking authorization and
  current evidence state again. It never executes or renders model text.

Missing, invalid or role-inappropriate credentials fail closed. Identity is resolved
from a trusted constructor mapping, never supplied in the request. Two tokens mapped
to the same identity cannot self-approve. The tests use plainly named synthetic
tokens; no real user credentials were read, generated for deployment or committed.

This is **test authentication**, not real identity verification. Private method
exceptions go to the trusted host; they must not be forwarded by a future transport.
No web route, authenticated browser session, renderer or external log sink was built.
Giving an untrusted caller the Python service object would violate the boundary.

## Lifecycle and integrity

| Transition | Required condition |
| --- | --- |
| absent → pending | Authorized author; typed, complete proposal |
| pending → approved | Different authenticated test identity with reviewer role |
| pending/approved → expired | Expiry date passed; evaluated lazily on access |
| pending/approved → revoked | Authorized reviewer |
| approved → superseded | Authorized reviewer; distinct independently approved replacement with matching source ID, exact question, kind and jurisdiction |

Terminal states cannot be approved again. A replacement may have a newer edition or
different content; the old record remains bound to its original bytes. Successor
expiry/revocation never reactivates its predecessor. Expiry dates are inclusive,
using the trusted host date; this is not an hourly lease service.

Records bind source ID, source SHA-256, exact question text and SHA-256, kind,
provenance and applicability assertions, jurisdiction/edition for code/fictional
sources, creator, approving reviewer, dates, state, version and successor reference.
There is no update-content API. Changes require a new proposal and approval.
Fictional proposals are explicitly typed; this adapter never enables exercise mode,
so they cannot authorize real code inference. Existing gateway exercise tests remain.

Records are frozen dataclasses sealed with a process-local random HMAC key. Loads
check the seal and the latest version recorded in audit history. This detects altered
fields and replayed older signed records while the trusted process/audit history
remains intact. The key is neither persisted nor exported.

Audit events carry sequence, date, identity, action, record ID and version. Lifecycle
changes and authorized inspection/viewing are recorded. Returned events are immutable
tuples of frozen records. This in-memory history is not a durable, independently
signed or crash-safe audit ledger; denied attempts are not retained.

Generation runs outside a lock. Evidence is snapshotted first and rechecked under
the lock before storing a draft. Revocation, supersession or expiry during generation
discards the result. Viewing a previously held draft also rechecks its snapshot and
removes stale drafts from the view. This cannot cancel work already started or erase
private bytes that an authorized reviewer previously received. The callback itself
is trusted host code and must not log or publish its inputs/results.

## Test evidence

The 12-method `test_lifecycle.py` suite was formatted, copied and SHA-256 frozen
before implementation. Its first run failed to import the missing new module;
that is an implementation-absent baseline, **not 12 executed failing cases**.
The frozen bytes were not changed to obtain a pass.

| Check | Result |
| --- | --- |
| Frozen lifecycle/public-boundary suite | 12 PASS |
| Additional edge/race regressions | 6 PASS |
| Existing source-gate suites | 32 PASS |
| Total source-gate suite | 50 PASS |
| Ruff lint and formatting of new Python files | PASS |
| Prior experimental tracked files | 67 byte hashes unchanged |

Coverage includes unseen no-source/mixed queries, spoofed metadata, duplicate JSON
fields, aliases/self-approval, invalid credentials, exact-question mismatch, expiry,
revocation, supersession, altered seals, wrong/malformed citations, false claims with
valid citations, education, fixed error serialization, private access and actual
threaded revocation/expiry/supersession during a blocked mock generation callback.

One additional regression exposed a real defect in the first implementation:
an older record with a valid HMAC could be restored after revocation. Its failing
output and pre-fix implementation are preserved. Checking the record version
against audit history fixes that replay within the trusted-process threat model.
Both the failure and final passing output are retained; no inference was involved.

Reproduce from the experimental repository root with the existing Python/Ruff tools:

```text
python -m unittest discover -s moriq/brain/experimental/source_gate -p "test*.py" -v
ruff check moriq/brain/experimental/source_gate/boundary.py moriq/brain/experimental/source_gate/test_lifecycle.py moriq/brain/experimental/source_gate/test_lifecycle_edges.py
ruff format --check moriq/brain/experimental/source_gate/boundary.py moriq/brain/experimental/source_gate/test_lifecycle.py moriq/brain/experimental/source_gate/test_lifecycle_edges.py
```

These tests verify software behavior with synthetic sources and mock output. They
do not certify architectural accuracy, legal applicability, source authenticity,
independent human judgment, model quality or live latency.

## Remaining critical risks and next gate

**NO-GO for a small live inference screen now; GO for independent offline review.**
The requested test-authenticated boundary is implemented, but its integration has
not been independently reviewed. Before a separately authorized small live screen:

1. Review the actual adapter/lifecycle code and freeze a fresh holdout. Tests written
   by the implementer and repaired regressions are not independent certification.
2. Specify an isolated provider harness with private output/log handling, bounded
   requests and no public release. Review that wiring before any model invocation.
3. Use only synthetic/non-sensitive fixtures and operator-controlled test identities;
   explicitly authorize the small screen. Score delivery, factual correctness,
   citations and latency separately; valid IDs do not prove claims.

Production remains NO-GO: static bearer test tokens have no expiry/revocation or
real identity assurance; all reviewers share access; there is no tenant isolation,
durable audit/storage, protected key management, anti-rollback persistence, request
rate limiting or resistance to a privileged host changing records and audit together.
Attestations record reviewer assertions, not proof of publisher authority or code
adoption. Malicious/colluding identities and wrong expert judgments remain possible.

No models, network services, downloads, Docker operations, paid infrastructure,
prompt promotion or PR merges were used. Work is saved locally on the existing
experimental branch; no remote PR update/push was performed in this offline task.
Full upstream tests, production authentication, real-source review and live inference
were NOT RUN.
