# Task 3.6.1 — bind signed attestations to their registry identity

October 14, 2026. Local branch: `feature/brain-v0.2-experiments`.
HEAD remains `9f487f08faef3fe09418b259232bbbabc8c39d04`.
**Registry-ID defect fixed; GO for code review, NO-GO for live inference.**

## Exact cause and narrow fix

Task 3.5 signed the record contents with HMAC but omitted the registry lookup ID.
Two approved records could have equal versions. Copying the second record/seal
pair under the first registry key passed both its MAC and the version check,
despite resolving the requested reference to different evidence. The Task 3.6
regression reproduced this before editing: one test method failed two assertions,
returning `review_required` and making one mock generation call.

Only `boundary.py` changes existing implementation behavior:

- `Record` now requires an immutable `registry_id`, populated by the existing
  creation flow using its generated registry key.
- `_seal(key, record)` rejects missing IDs, non-string IDs, noncanonical lookup
  keys and any mismatch between the signed record identity and the lookup key.
  Canonical registry IDs are exactly 32 lowercase ASCII hexadecimal characters;
  no trimming, case folding or alternate representation is accepted.
- The signed payload is a JSON object containing the format discriminator
  `moriq-attestation-v2` and the entire record, including its registry ID.
  Serialization sorts keys, uses compact separators, ASCII escaping, UTF-8 bytes
  and rejects NaN. Validated date fields are explicitly encoded as ISO dates.
  There is no generic `default=str` fallback or ambiguous string concatenation.
- Both save and load use the same identity-bound signing function. Editing the
  embedded ID to match a transplanted lookup key still invalidates the signature.
  The existing audit-version check remains and still rejects older valid records.

Independent approval, exact question/source hash, jurisdiction/edition, expiry,
revocation, supersession, source eligibility, private authorization and public
response construction are unchanged. No provider harness was built.

## Migration: intentionally fail closed

Pre-binding records without `registry_id` are rejected. Legacy seals are rejected
even if someone adds the correct ID to the record; there is no old-format retry,
auto-resigning or migration switch. All newly created records use the v2 payload.

This prototype has only in-memory records and a process-local signing key, so
there is no supported persistent-store migration. Preserve old evidence for audit;
if continued experiments require attestations, create new proposals through the
normal author workflow and obtain independent approval again. Do not import old
approvals as trusted or automatically rewrite their identities. No existing
runtime instance or application data was migrated, restarted or modified.

## Tests and preservation

The previously failing Task 3.6 regression ran first and its failure output was
saved. It ran unchanged immediately after the fix and passed with zero mock calls
for the substituted record. Existing tests were not weakened or rewritten.

Six new `test_registry_binding.py` methods cover legitimate records with equal
contents/versions but different IDs and seals; missing/malformed/tampered IDs;
transplanting a seal while rewriting its embedded ID; legacy seals; same-ID replay
after revocation; and canonical payload construction/rejection before signing.

| Check | Before | After |
| --- | --- | --- |
| Original substitution regression | FAIL: 2 assertions, 1 mock call | PASS: rejected, 0 calls |
| Source-gate suites, including adversarial, boundary and lifecycle | Historical Task 3.6: 55 PASS / 1 FAIL | 62 PASS |
| Prior V0.2 tests | Initial sandbox temp-directory error retained | 4 PASS on retry |
| Prior V0.2.1 screening tests | — | 3 PASS (mocked streams) |
| Original Brain tests | Initial sandbox temp errors/asyncio timeout retained | 8 PASS on retry |
| Unique tests in final successful suites | — | **77 PASS, no skips** |
| Ruff lint / formatting | — | PASS; 21 Python files formatting checked |
| Prior tracked experimental hashes | 67 | 67 unchanged |
| Existing uncommitted files | 19 snapshotted by hash | 18 unchanged; only boundary.py edited |

The initial environment failures are not hidden. Retries used a workspace temporary
directory and granted socket permission for Windows asyncio event-loop setup.
No model/provider endpoint was called. All generation and screening transport
behavior in these tests is mocked; Brain tests exercise builders and isolated
upstream helpers. No live inference, latency or human source verification occurred.

Public/private tests still verify that draft text, sensitive metadata, internal
result text, unknown statuses and exception text do not enter the fixed public
JSON. Missing reviewer authorization prevents private serialization. A callback
that prints can still emit private data to stdout; that known trusted-host limit
is unchanged and must be addressed by any future harness's output isolation.

Reproduce from the repository root with the existing local tools:

```text
python -m unittest discover -s moriq/brain/experimental/source_gate -p "test*.py" -v
python -m unittest discover -s moriq/brain/experimental/v02 -v
python -m unittest discover -s moriq/brain/experimental/v021 -v
python -m unittest discover -s moriq/brain/tests -v
ruff check moriq/brain/experimental/source_gate moriq/brain/tests moriq/brain/experimental/v02/test_experiment.py moriq/brain/experimental/v021/test_screen.py
ruff format --check moriq/brain/experimental/source_gate moriq/brain/tests moriq/brain/experimental/v02/test_experiment.py moriq/brain/experimental/v021/test_screen.py
```

## Changed files and evidence

- Modified: `boundary.py` only (identity field, signing/verification, creation call).
- Added: `test_registry_binding.py`, this report, and `binding_evidence/` logs/hashes.
- Original Task 3.5/3.6 reports, frozen tests, failures and proposed PR text remain
  preserved as historical evidence. A new proposed PR update records this fix;
  nothing was published. The exact implementation diff is saved with the outputs.

## Remaining gates and risks

The record-substitution gate is now satisfied by offline evidence. **NO-GO for a
small live inference screen remains:** no isolated provider harness has been built
or reviewed, and its streaming/error/log/cancellation boundaries are unverified.
Task 3.6's remaining checklist still applies: freeze a tiny manifest, verify actual
public output sinks and private results access offline, specify CPU/concurrency/
time/token limits, and obtain explicit approval before invoking a model.

Test tokens are not production identity; reviewers share access; audit history and
keys are in memory. A privileged host can alter records and history together.
HMAC proves consistency with that process key, not source authenticity, authority,
code adoption, applicability or factual correctness. Real-source use still needs
qualified independent human verification. No automatic answer release exists.

No commits, pushes, PR updates, merges, model calls, downloads, deployments,
credential changes, paid services or prompt promotions occurred.
