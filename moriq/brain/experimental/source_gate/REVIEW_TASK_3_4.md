# Task 3.4 — independent adversarial code review

What this change does: the prototype prevents inference for source-required
questions without reviewed evidence and checks source identifiers on drafts.
This review inspected its actual code, every caller, tests and evidence, and
found that the old public result still carried the supposedly private draft.

Reviewed baseline: PR #12, commit `05a7d9de721bc81da51e5198bef2aed49272b98d`,
draft/unmerged. Scope: the isolated Python library with trusted in-process host
configuration, one request at a time; no production UI, authenticated review
service or live provider exists. This is a fresh Codex review with separately
written tests, not review by an external architectural expert or security auditor.

## Must fix — now fixed inside the prototype

1. **P1: private draft returned in the public result** (`gateway.py`, old lines 96–101).
   **What this is:** `Result` combined fixed user prose with `review_draft`.
   **Problem:** `json.dumps(dataclasses.asdict(result))` and `repr(result)` both
   exposed a deliberately false legal claim marked `SECRET_REVIEW_ONLY`; checking
   only `result.answer` missed this. No existing production UI leak was observed:
   the reproduced defect is the library's unsafe serialization contract.
   **Fix:** remove draft data from `Result` entirely; send it only to a separately
   configured trusted reviewer sink. No sink means discard. Sink errors return
   fixed messages. Public serialization and representation are tested.
   **If skipped:** a normal future JSON response could publish held model prose.

2. **P2: caller mutation changed the validated source-ID set** (`Gateway.respond`).
   **What this is:** evidence was checked before generation, then the same mutable
   caller list was read again for citation validation.
   **Problem:** a callback appending unreviewed document 99 let `[99]` pass after
   only document 7 had been reviewed. This is a caller-mutation/concurrency case,
   not evidence that remote model text can execute Python.
   **Fix:** snapshot the document sequence before any validation or callback.
   **If skipped:** allowed identifiers could differ from the reviewed evidence.

3. **P2: hidden or linked citation text passed the syntax gate** (`citations_valid`).
   **What this is:** a regular expression collected bracketed numbers.
   **Problem:** `[7](javascript:alert(1))`, a data-URL link, `<!-- [7] -->` and an
   uppercase `HTTPS://` fabricated URL all passed. No browser exploit is claimed;
   there is no renderer here. They violate the plain citation protocol and may
   hide or redirect a marker in a future renderer.
   **Fix:** reject HTML markup and Markdown citation links, and match HTTP schemes
   without case sensitivity. Preserve strict ID membership and malformed-marker
   checks. This remains a bounded syntax validator, not an HTML sanitizer.
   **If skipped:** marker presence could be mistaken for a visible source citation.

4. **P2: malformed operator attestations were accepted** (`Gateway.__init__`, `applies`).
   **What this is:** Python dataclass annotations did not enforce metadata types.
   **Problem:** `provenance=None`, a string expiry date, a metadata dictionary or
   a non-hash question identifier entered the registry; some fail later with
   type errors rather than a controlled configuration rejection. This is not
   proof that an upload could self-approve: that path does not exist.
   **Fix:** validate record type, text fields, canonical hashes/IDs, date types,
   kind and exercise/sink configuration at construction. Empty rationale and
   expired/altered records still fail eligibility without generation.
   **If skipped:** invalid trusted configuration can break request handling.

## Should fix — bounded usability fix applied

5. **P2: ordinary education was refused, sometimes labeled company policy** (`route`).
   **What this is:** the prior exact-question list intentionally over-refused.
   **Problem:** all seven frozen new education phrasings failed; "How do internal
   partitions differ from load-bearing walls?" was classified as company policy
   because of "internal". That limitation now conflicts with Task 3.4's explicit
   education requirement; it is not presented as a newly discovered secret risk.
   **Fix:** add bounded whole-question grammar for conceptual explanations and
   reading questions about named architectural topics, plus the partition
   comparison. Appended code/policy/injection requests still block. No arbitrary
   text slot or substring match grants inference.
   **If skipped:** users would need company evidence for ordinary learning.
   Unrecognized phrasing still deliberately blocks; broad semantic routing is
   not implemented or certified.

## Frozen evidence and results

The question corpus and adversarial test source were frozen and hashed **before
editing the implementation**. Baseline copies of all five Task 3.3 files are
preserved. The same suite bytes ran before and after fixes; dates in synthetic
attestations are relative to execution day to test expiry reliably.

| Check | Baseline | After fixes |
| --- | --- | --- |
| Frozen adversarial test methods | 6 PASS, 6 FAIL | 12 PASS |
| Failed assertions including subtests | 18 | 0 |
| Full source-gate suite | Historical Task 3.3 result preserved | 32 PASS |
| Lint / formatting / scoped whitespace | Checked after changes | PASS |
| Prior V0.2 / V0.2.1 evidence | 31 hashes verified | Unchanged |

The frozen corpus contains 11 new source-required/ambiguous questions, seven
education questions, 28 education-plus-injection/mixed combinations, and 11
malformed citation strings. Additional tests cover upload metadata spoofing,
altered/expired attestations, fictional/real scope, list mutation, and valid IDs
attached to false claims. All no-source cases explicitly assert zero callback
calls. Original tests were adapted only for the intentionally removed public
draft field; their original bytes and results remain in the baseline snapshot.
Five focused tests exercise private handoff, absent/failed sinks, discarded
drafts, gap/citation rejection before handoff, and type-confused exercise mode.

There was a transient local test migration error when a Windows default text
decoder could not read the Unicode test file. No write occurred; using explicit
UTF-8 allowed the caller tests to be updated. The frozen adversarial suite was
not changed to make it pass.

These questions were new to the saved project evaluations. After being used to
guide fixes they are regression tests, not an untouched post-fix holdout. No
architectural correctness, legal authority, model injection resistance or model
latency is established by mock callbacks and source-ID tests. A false claim with
a valid ID intentionally still passes citation syntax and stays review-only.

## Remaining boundaries and go/no-go

**NO-GO for a live inference screen yet. GO for offline prototype review.**

The library's public `Result` now contains only fixed strings; tests cover its
serialization and representation. There is no other user-facing adapter in the
repository. It is therefore inaccurate to claim that *every future UI/output*
is proven unable to leak a draft. A trusted reviewer callback can publish its
input if wired incorrectly, and no authenticated reviewer-only storage/view
exists. Likewise, operator attestations remain assertions by trusted host code,
not cryptographically authenticated provenance or verified legal applicability.
Malformed metadata rejection does not stop a malicious privileged operator from
writing a well-formed false attestation. Revocation and reviewer authorization
remain outside the implemented boundary.

Before a later **small**, explicitly authorized live screen:

1. Supply and review an isolated adapter whose end-user response is constructed
   exclusively from `Result`; demonstrate that private reviewer output cannot
   be read through the public interface and that logging does not expose it.
2. Define the trusted reviewer sink/access controls and attestation lifecycle.
   Use fictional fixtures only until qualified people verify real provenance,
   adoption, project scope and applicability. Do not treat source labels as proof.
3. Freeze a fresh holdout with broader paraphrases and mixed intents. Record
   false accepts, false refusals, zero-call gaps, withheld outputs, factual
   correctness, citations and latency separately. Do not grade claim accuracy
   solely by valid IDs or repeat this repaired suite as an independent holdout.

No model inference, download, paid service, production change or merge occurred.
No network calls or provider integrations were added to the prototype. Existing
PR #11 and prior evidence are preserved. Full upstream application tests, real
reviewer access control and a live model evaluation were **NOT RUN**.

Verdict: fix the live adapter/reviewer-access prerequisites before a live screen;
the five isolated code defects above are fixed and regression-tested.
