# Task 3.3 — source-enforcement prototype

October 14, 2026. **Implemented and tested offline; not deployed.**

PR #12 was reviewed at `eb5cb8dff1c8b74b0a7f317e53e5a8a1d32fb74c`, draft and
unmerged. Its Instruct evidence confirmed unsupported OBC requirements after a
source-gap disclaimer, and two failures of the required [4] citation format.
Those exact saved inputs/answers now participate in regression tests. No prior
results or ratings were overwritten.

## Implemented behavior

- Unrecognized, ambiguous, company-policy and code/compliance questions without
  reviewed evidence return deterministic source-gap/clarification prose with
  **zero model calls**. No numeric requirement is inserted into those responses.
- A closed list of whole general RCP, floor-plan/section and thermal-bridge
  questions permits educational drafts without company documents. Unknown
  paraphrases deliberately block. Mixed requests must be separated or have the
  necessary reviewed evidence for the exact question; there is no automatic
  sentence splitting.
- Uploaded documents confer no trust. Operator attestations bind content hash,
  exact question, source ID, kind, provenance/applicability rationale, reviewer,
  dates and code jurisdiction/edition. There is no request-time approval flag.
  This records a human review; it does not authenticate or perform that review.
- Fictional evidence cannot satisfy the normal real-authority route. It requires
  explicit exercise mode and a matching fictional review, and stays labeled.
- Citation validation rejects missing [4], unknown IDs, mismatched declared IDs,
  malformed markers and common Unicode variants. It never repairs citations by
  guessing a source. Valid IDs alone do not validate facts.
- All generated text, including general education, stays in an internal
  `review_draft`. The user-facing `answer` is fixed text, and no release method
  exists. An intentionally false claim bearing valid [4] remains review-only.

The implementation is confined to `moriq/brain/experimental/source_gate/` on
`feature/brain-v0.2-experiments`. It has no network calls, provider adapter,
document importer, production hooks, or new dependencies.

## Results

| Check | Result |
| --- | --- |
| New source-gate unit tests | 15 PASS |
| Original Brain unit tests | 8 PASS |
| V0.2 experiment unit tests | 4 PASS |
| V0.2.1 screening unit tests | 3 PASS |
| Ruff lint and format | PASS |
| Prior committed evidence hashes | 31 unchanged |
| Live inference, answer-quality evaluation and model latency | NOT RUN |
| Production integration, deployment and merges | NOT RUN |

Tests cover code paraphrases, ambiguous/mixed queries, question/document
injection, spoofed approval, altered/expired/duplicate reviews, kind mismatches,
fictional fixtures, general education, source identifiers, provider failures and
the distinction between valid citations and true claims. All generation uses
mocks. Test success proves these control-flow checks, not model reliability.
See `validation.json` for individual test names and exact test output.

The first regression attempt stalled at the existing Windows `asyncio` test
with restricted loopback sockets and was interrupted. After granting loopback
access for the event loop, all suites completed successfully. No inference or
HTTP provider call was added or executed. This was an execution-environment
limitation, not a source-gate test pass or model failure.

## Limits and next gates

The education catalog intentionally over-refuses; it is not a general semantic
classifier. The review registry is trusted in-process host configuration, not
an authenticated source-management service. A malicious operator could enter
false attestations. Citation parsing covers a defined syntax, not arbitrary
plain-text references or claim entailment. Prompt-injection resistance inside
a real model remains untested; no-call gating and draft withholding are the
implemented controls. A consumer must never expose held drafts as final answers.

Before further model experiments: independently review routing, trust boundaries
and draft handling; create an authenticated provenance/applicability review
workflow; and prepare an unseen adversarial test set. After approval, use a small
isolated screen with the original twelve cases plus unseen questions, scoring
no-call behavior, routing, factual correctness, unsupported claims, completion,
citations and latency separately. Broader repetitions and any deployment need
separate review and authorization. Citation checks alone are not sufficient.

No model was pulled or called, no paid service was used, and no current deployment,
credential, Docker data, original Brain or PR #11 was changed.
