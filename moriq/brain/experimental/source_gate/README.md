# Task 3.3 — isolated source-enforcement prototype

Status: **offline prototype, not a production safeguard or approved replacement**.
No network adapter, model connection, document ingestion, Open WebUI integration,
deployment configuration, real code corpus or automatic answer publication exists.
Only this new experimental directory changes. V0.1, prior experiments and their
evidence remain unchanged on `feature/brain-v0.2-experiments` / draft PR #12.

## Why this exists

The Instruct-2507 screen in `../v021/evidence/` showed that both prompts could
acknowledge missing OBC extracts and then invent numeric requirements and section
references. One fictional-rule answer omitted [4]; the other used the wrong
marker format. Faster delivery and a stronger prompt did not enforce the evidence
boundary. The prior qualitative ratings are screening judgments, not independent
architectural certification; this change uses exact saved inputs/answers as
regression data without altering their ratings or claiming the prototype fixes
the model's knowledge.

## Decisions outside the model

`Gateway.respond(question, documents, generate=callback)` is a library API for
tests and future isolated experiments. The callback is supplied by trusted host
code. This repository supplies no live callback or executable inference path.

| Input | Decision before any callback |
| --- | --- |
| Exact recognized general RCP, floor-plan/section or thermal-bridge question, no documents | Permit an educational draft; no company evidence required. |
| Company policy or jurisdiction/code request without eligible evidence | Return fixed source-gap prose, no model call, no invented numbers. |
| Unknown paraphrase, ambiguous request or unfamiliar education question | Return fixed clarification/source-gap prose, no model call. |
| Mixed company/code request | Require eligible evidence of both kinds for the exact combined question. |
| General question plus uploaded material | Clarify scope; do not forward untrusted material through the education exception. |
| Fictional fixture | Never real authority; requires explicit trusted exercise mode and a matching fictional review. |

The education catalog and bounded grammar are intentionally closed and matched against the **whole**
normalized question. Keyword searches label rejected requests; they never grant
education access. An appended instruction, unknown language or clever code
paraphrase therefore defaults to blocking, even if no risk keyword is recognized.
This has high false-refusal cost. It is not a general natural-language intent
classifier. For mixed education/compliance questions, the prototype blocks the
whole question and asks the user to separate it; it does not attempt unreliable
automatic sentence splitting. Do not widen this gate using substring checks.

## Trust boundary and evidence review

Uploads contain only `Document(id, text)`. Words such as "official", an HTTPS
address, a source label, a model judgment, and correctly formatted citations do
not grant authority. There is no user-controlled `verified=true` field.

A trusted operator must first verify the publisher/owner and provenance,
document integrity, current approval/adoption, jurisdiction and edition, relevant
project facts, scope/exceptions, and conflicts/supersession. Then trusted host
code may supply a `Review` registry at construction. Each review records:

- exact source ID and UTF-8 content hash;
- exact question hash (including all facts supplied in that question);
- company, code or fictional kind;
- provenance and applicability rationale, reviewer, review and expiry dates;
- jurisdiction and edition for code/fictional exercises.

The gate checks these bindings, required fields, dates, source uniqueness and
kind coverage. Changed text, changed question, expired/duplicate reviews or any
extra unreviewed document block generation. Review metadata is an **operator
attestation, not automated verification**. This process is not implemented or
authenticated by the prototype. All test reviews are synthetic test doubles;
there is no verified Ontario code source or company corpus in this experiment.
A service must never deserialize user-provided review records into this registry.
Authenticated review management, revocation, project-context identity and access
control remain prerequisites to any integration. Exact question hashes trade
reusability for conservative scope; even harmless paraphrases need a new review.

## Citation gate and release boundary

The callback returns a typed `Draft(text, source_ids)`. The document sequence is
snapshotted before validation so later caller mutation cannot change allowed IDs. Required-source drafts
must have at least one exact ASCII `[id]`, all declared IDs must match the inline
IDs, and every ID must belong to the reviewed evidence supplied on that request.
Unknown, duplicate declared, missing, malformed and common Unicode-lookalike IDs
are rejected. Bracket variants, HTML markup, Markdown citation links and model-written HTTP
links (regardless of case) are unsupported.
The exact `[source id="4"]` output from the screen is deliberately rejected.
No automatic citation repair invents a connection between a claim and a source.

This validates a **limited citation syntax and membership protocol only**. It
does not establish entailment, completeness, applicability of every generated
claim, numeric correctness, source truth, or absence of injection. Plain-text
invented section names can evade citation parsing. A false claim with a valid
[4] intentionally passes the syntax check in a regression test.

Consequently **no model prose is present in the returned `Result`**, including
its dataclass serialization or representation. Trusted host code may configure
`review_sink=callable` at gateway construction to receive a separate `ReviewerDraft`.
With no sink, the draft is discarded. `Result.answer` contains only fixed messages.
There is no release method. A consuming UI must never serialize the private sink
item as a public response or treat `review_required` as PASS. The sink is a trusted
capability, not an authenticated reviewer service; authorization remains unimplemented. The model has no tools in this prototype;
source text is passed separately as untrusted evidence, with an instruction to
ignore embedded commands. That instruction is not claimed to resist injection:
the deterministic protection is no-call gating and no automatic draft release.
Generation errors suppress model/error prose rather than leaking it to users.

## Offline validation and reproduction

From the repository root:

```powershell
python -m unittest discover -s moriq/brain/experimental/source_gate -v
ruff check moriq/brain/experimental/source_gate
ruff format --check moriq/brain/experimental/source_gate
```

The tests use `unittest.mock.Mock`, never Ollama or a paid API. They cover saved
OBC questions and missing [4] answers, unfamiliar/paraphrased code requests,
mixed/ambiguous questions, source-borne and question-borne injection, approved-label
spoofing, altered/expired/duplicate reviews, fictional-source isolation, exact
source IDs, and the three general education topics. They assert callback absence
for source gaps and demonstrate that valid citations can accompany false claims.
These are control-flow tests, not live behavior, legal correctness or latency tests.

## Proposed evaluation gates (not executed)

1. **Routing/security review:** independent adversarial set covering paraphrases,
   multilingual/Unicode text, appended instructions and mixed intents. Report
   false refusals and source-required false accepts separately. No source-required
   request without reviewed evidence may invoke the model. Verify the consumer
   never displays held drafts as released answers.
2. **Evidence workflow:** verify actual provenance/adoption/scope review with
   qualified reviewers, authenticated operator records, expiry/revocation and
   conflicting sources. Synthetic attestations cannot pass this gate.
3. **Small live isolated screen, only after approval:** reuse the original twelve
   cases plus frozen unseen questions. Score routing, no-call behavior, factual
   correctness, unsupported claims, delivery, citations and latency separately.
   Code/company source gaps should produce deterministic responses; supplied
   fictional fixtures must stay exercises. Preserve every failure.
4. **Claim review:** independently check claims against actual reviewed excerpts,
   including deliberately wrong claims with valid citations. Citation validity
   never cancels factual or evidence failure. Decide an authenticated release
   mechanism before exposing drafts; none is supplied here.
5. **Broader repeated evaluation and integration:** only after earlier gates and
   separate authorization. Keep CPU tests bounded, use one loaded model, preserve
   the deployed instance, and verify access control and prompt/source composition
   in an isolated environment before considering deployment or merge.

## Task 3.4 review

See `REVIEW_TASK_3_4.md` for five reproduced defects, isolated fixes, frozen
adversarial baseline/post-fix results and the live-screen go/no-go decision.
The Task 3.3 `RESULTS.md` and `validation.json` are preserved historical evidence;
the returned-draft contract described there was superseded by this review.
