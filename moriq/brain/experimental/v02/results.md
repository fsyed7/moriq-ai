# Task 3.1 comparison

**No candidate is accepted for deployment.** The experimental V0.2 prompt and
disabled import artifacts are separate from the working V0.1 model. No existing
Docker data, credentials, application settings, sharing or model configuration
was changed. Qwen3.5 2B was added as an experimental Ollama tag; no tag was replaced.
The repository's `case-results.md` lists every case and separate score dimension;
`evidence/` preserves exact requests, final answers, thinking, reviews, model
metadata and SHA-256 manifest. Local deliverables also include a readable full
answer review. Findings are Codex's rubric-based review, not independent expert
certification or a statistical model benchmark.

## Method

Observations were collected October 12, 2026 in America/Toronto; the evening
continuation has October 13 UTC timestamps. The long pause between sessions was
outside individual completed Qwen3.5 requests and is not included in their latency.

Base: `develop` commit `1a9d5a973bd5205f74d512b2bc417f2c7e00abb9`.
Branch: `feature/brain-v0.2-experiments`. The deployment work remains on separate
draft [PR #11](https://github.com/fsyed7/moriq-ai/pull/11), checked open/unmerged
before publication. This branch changes only the experimental Brain directory.

The unchanged twelve cases and synthetic fixtures in `../../evaluation.md` were
used with fresh provider message arrays, no tools and no retrieval. V0.1 has 792
whitespace-separated words; V0.2 has 373. Canonical stripped UTF-8 prompt hashes:

- V0.1: `b9c37e08797a79b0afbcfb716bc1ff57a1a751d02134ed6d776319beb568e2e0`
- V0.2: `c4a8c7b84c062cd0eabc7248becc380988969ca7d3623159c79d5b32cc2e1cc7`

Within each model, prompt comparisons use identical seed 101, context 4096,
generation limit 1500, temperature 0.2, top-p 0.95, top-k 20, repeat penalty 1,
presence penalty 0 and keep-alive 5m. Qwen3 uses `/no_think` appended to either
prompt; Qwen3.5 uses API `think:false` for either prompt. These are not equivalent
thinking controls across models, so the cleanest comparison is **within** each
model. Later metadata/model-card verification established that installed Qwen3
is Thinking-2507, which does not support non-thinking mode. The soft marker is
therefore a preserved ineffective intervention, not a demonstrated switch.
Model sizes, quantization and tokenizer also differ. This screening uses
one observation per case, not three acceptance repetitions. Runs were sequential
on a shared CPU host; fixed order, cache state and cold loading limit causal
latency claims. No experimental prompt was edited between these observations.
The controlled settings also differ from the downloaded Qwen3.5 defaults
(temperature 1 and presence penalty 1.5). In particular, no repetition/presence
penalty may contribute to repetitive output. This experiment rejects the tested
configurations; it does not establish that either model fails under every setting.

The historical V0.1 run used default provider sampling/thinking rather than these
controlled settings. Its 2/12 case passes and 217.670-second median are contextual
baseline evidence, not a prompt-only controlled comparison. Its interrupted
20,755.636-second request is excluded from historical latency statistics.

## Measured results

The controlled Qwen3 V0.1 run has 12 observations, 2 narrow rubric passes,
1 overall pass, and 5/12 nonempty natural completions. Its 11 valid timings range
from 66.688 to 317.719 seconds, median 221.906 seconds. Median first-answer time
among valid runs with visible answers is 95.406 seconds; empty answers are not
silently treated as zero latency. The interrupted fictional-code request is
excluded from timing but retained as a failed case.

| Model / prompt | Case rubric PASS | Overall PASS | Delivered to provider stop | Median total | Median first answer | Valid total range |
| --- | --- | --- | --- | --- | --- | --- |
| Qwen3 4B / V0.1 | 2/12 | 1/12 | 5/12 | 221.906 s | 95.406 s | 66.688–317.719 s |
| Qwen3 4B / V0.2 | 5/12 | 4/12 | 10/12 | 94.562 s | 84.125 s | 45.516–188.515 s |
| Qwen3.5 2B / V0.1 | 3/12 | 2/12 | 11/12 | 71.242 s | 8.563 s | 9.438–166.891 s |
| Qwen3.5 2B / V0.2 | 3/12 | 2/12 | 12/12 | 17.391 s | 7.970 s | 8.437–33.140 s |

All 48 planned screening observations were reviewed, including one interrupted
partial answer. A separate connection-denied attempt is not a behavioral run.
No tool calls were emitted in any observed response. Qwen3 V0.2 improved the
company naming/source-gap/injection responses and Toronto-context handling.
Its four overall passes contain no identified unsupported MORIQ-policy claim.
However, it refused general architecture/design questions, omitted teaching
criteria, exhausted the cap with empty RCP and one-sentence answers, and omitted
[4] even when its final fictional-code reasoning was correct. Its approximately
57% lower total median therefore does not justify deployment. First-answer
medians exclude empty answers and do not represent successful-delivery rates.

Both Qwen3.5 runs returned zero separate thinking text. The shorter prompt reduced
total time mainly by producing shorter final answers; first-answer medians barely
changed. Its roughly 76% lower total median is **not** an accuracy improvement.
Median generated tokens fell from 621.5 to 122.5. Maximum reported prompt tokens
plus the 1500-token allowance were 2766 and 2184 respectively, below context 4096;
these observations do not indicate simple context-window overflow.
V0.1's door-schedule tutorial degenerated into repetition and reached the cap.
V0.2 finished every stream, but several answers were semantically incomplete.

V0.2 handled the unsupported naming-policy question proportionately without
inventing policy. However, it misdefined RCP as Residential Code Plan, echoed
system instructions in a tutorial, ignored conflicting values/citations, and
refused the fictional code reasoning exercise despite sufficient supplied data.
The short source-gap rule appears overgeneralized to tasks it should not block.
V0.1 misdefined RCP differently, fabricated Ontario code claims, and gave an
unsupported grid-compliance claim. Neither prompt passed the knowledge/teaching
gate. In injection answers both rejected the malicious instruction but still
made unsupported negative claims about policy existence.

Case-rubric PASS and factual review are deliberately separate. For example, both
code-no-jurisdiction answers ask the required missing context without inventing
a width, but cite misleading code examples and promise unavailable search. They
meet that narrow case rubric while failing the broader factual/capability review.
Requiring rubric PASS **and** factual PASS **and** complete delivery leaves only
**2/12 overall passes for each Qwen3.5 prompt**. The case table shows all three
dimensions and the overall gate. Reviewer-identified unsupported company claims
occur in 2 V0.1 answers versus 1 V0.2 answer; unsupported code claims occur in 4
versus 1. These count affected answers, not individual claims, and do not imply
other answers are accurate. Reduced fabrication came with over-refusal and errors.
An empty final answer is NOT ASSESSABLE for factual correctness and FAIL for the
case/delivery gate; it is never counted as a hallucination-free success.

## Evidence preservation and deployment boundary

Original baseline raw JSONL SHA-256:
`1eeffe96cc863ca2abdbf31195af1ada6e5afd380ff369bbd0f721c5b2ae1afa`.
Original V0.1 import artifact SHA-256:
`fc1518140343ef0cb3e5c4587d540b5b457cebb2c3e52efe3b4387de5c433991`.
Both remained unchanged. The prior readable baseline is preserved at
[deployment commit 567e433](https://github.com/fsyed7/moriq-ai/blob/567e4332e68e391579cb110c6504b70335e382ec/docs/LOCAL_BRAIN_EVALUATION.md).

The resumed shell initially denied localhost with WinError 10013 before sending
the Qwen3 general request. That transport attempt is preserved in `screen.jsonl`
and is NOT RUN for behavior, not a model failure or a valid latency. Network
permission was granted and the missing cases continued in a new JSONL file.
Completed screening cases were not repeated. Original review files are retained;
later reviews live in companion files rather than replacing earlier decisions.
The Qwen3 V0.1 fictional-code request later timed out after a long host pause
(707.953 s). Its partial answer is preserved and fails completion; that latency
is excluded. Ollama logged cancellation, slot release and all slots idle before
the missing V0.2 cases resumed. The failed request itself was not repeated.

Open WebUI returned HTTP 200 and version 0.11.4 during the experiment. Docker
health/mount/digest remain the previously verified Task 3 evidence; this work
does not claim a new named-pipe inspection. Experimental artifacts were not
imported. WebUI integration, retrieval citation rendering, access tests, other
local models and independent expert review are NOT RUN in this experiment.

## Recommendation

Keep deployment unchanged. Do not promote either tested V0.2 configuration.
Preserve the prompt as a failed experiment: its concise company-source response
is useful evidence, but its over-refusal and weak architectural knowledge are
unacceptable. A next experiment should scope the source-gap rule strictly to
company questions, compare the separate Qwen3 4B Instruct-2507 tag or a stronger
architectural model within measured memory,
and verify thinking control through actual final-answer delivery. Use unseen
architecture/source fixtures as well as this matrix, then run at least three
repetitions per case before selecting a candidate. No model or prompt alone
supplies an approved MORIQ knowledge library or authoritative project code source.

The eight existing Brain tests and four experimental isolation/parser/settings tests
pass. Ruff lint and formatting pass. These checks verify helpers and isolation,
not answer quality. Upstream application code and dependencies were not changed.
