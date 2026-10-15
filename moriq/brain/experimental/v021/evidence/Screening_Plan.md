# Instruct screening proposal â€” not deployed

Revision 0.2.1 clarifies that general education is allowed without MORIQ records.
The narrower evidence gates apply to company claims and code compliance. It also
allows answering the educational portion of mixed questions. V0.1 and V0.2,
their builders, raw results and reviews remain unchanged. This is an unvalidated
prompt revision, not a selected replacement or an Open WebUI import artifact.

## Evidence and model choice

Task 3.1 recorded 48 observations (47 completed streams and one partial timeout).
Overall passes were Qwen3/V0.1 1/12, Qwen3/V0.2 4/12, Qwen3.5/V0.1 2/12 and
Qwen3.5/V0.2 2/12. Completed streams include truncated or inaccurate answers.
The shorter prompt sometimes refused general education. Faster Qwen3.5 output
did not establish reliability. Keep these failures; do not rerun them as if lost.

The installed `qwen3:4b` is Thinking-2507. Its soft `/no_think` intervention was
ineffective. The proposed distinct download is
`qwen3:4b-instruct-2507-q4_K_M`, approximately 2.5 GB, published digest prefix
`0edcdef34593`; `qwen3:4b-instruct` currently aliases it. Verify the full local
digest and template after an approved download. No tag may be overwritten.

Sources checked October 12, 2026 local time:

- [Ollama exact tags](https://ollama.com/library/qwen3/tags)
- [Qwen Instruct-2507 model card](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507)
- [Ollama Instruct template](https://ollama.com/library/qwen3:4b-instruct/blobs/eade0a07cac7)

The model card describes non-thinking-only behavior. That is a reason to test,
not evidence of architectural correctness. No thinking toggle or template edit
will be applied to the working model.

## Proposed small screen

First compare canonical V0.1 against this revision on the **same Instruct model**.
Use six inputs: original `general`, `moriq-no-source`, `code-with-context`,
`code-source`, then unseen `plan-section` and `thermal-bridge`. One observation
per prompt/input gives twelve requests. Alternate which prompt goes first for
successive inputs. Freeze questions, rubrics and prompts before starting.
Report this screen before authorizing a larger repeated benchmark. A screen
cannot pass the full twelve-case release gate.

Request-local settings for both prompts: CPU `num_gpu:0`, `num_thread:4`, context
4096, output cap 1500, temperature 0.2, top-p 0.95, top-k 20, repeat penalty 1,
presence penalty 0, seed 101. No `/no_think`, tools, retrieval or chat history.
These controlled sampling settings preserve Task 3.1's baseline, but do not
claim to be the vendor's optimal settings. Do not alter global Ollama settings.

Begin only with no loaded models and no observed competing requests. Reserve
at least 5 GiB available physical RAM before loading (a conservative test gate,
not a vendor minimum); record available RAM before and during inference. Load
only this model, serially; verify `/api/ps` reports only it and `size_vram:0`.
Use `keep_alive:0` per measured request and confirm unload before the next one,
so both prompts have the same cold-load policy. Report load time separately;
OS file caching can still differ. Stop on low memory (below 1.5 GiB), another
model/request, transport failure, deadline or suspension. Do not queue retries
behind a possibly running request or terminate unrelated processes. A 360-second
deadline plus 30-second socket timeout needs monitoring; client cancellation
alone does not prove Ollama has stopped. Recheck idle state before resuming.

No automatic model downloads or inference are performed by the saved request
manifest. Approval is required for the missing model. Ollama has no exclusive
inference lock across unrelated clients: avoid concurrent WebUI chats during
the screen, observe the log, and mark contaminated timings invalid.

## Full matrix and scoring

Preserve the original twelve inputs and fixtures verbatim. Four new questions
and their rubrics are frozen in `unseen.json`; two are held out from the small
screen. They are new to this project's recorded evaluations, not guaranteed
absent from model training. Never insert their expected answers into the prompt.
After screen review, a possible larger test is all sixteen cases, three seeds
per prompt, alternating prompt order. It is **NOT RUN** and not automatically
authorized by this proposal.

Review full user-visible answers, not hidden reasoning. Score separately:

- **Factual correctness:** PASS/FAIL with specific claim review; NOT ASSESSABLE
  for no answer. Refusal of a general question also fails its task rubric.
- **Unsupported claims:** identify company, code and other unsupported claims
  separately. One fabricated company policy blocks acceptance.
- **Response delivery:** PASS only for nonempty, coherent, complete requested
  content with natural stop; empty, truncated, timed-out and off-topic fail.
- **Citation behavior:** required source IDs and faithful scope, no invented
  references or source-instruction obedience. General no-source education can
  pass without citations. Distinguish fictional reasoning from verified law.
- **Latency:** wall time, first visible answer, load/prompt/generation durations,
  token counts and tokens/second; flag invalid or interrupted observations.
  Do not turn faster output into a quality pass or invent a speed threshold.
- **Case rubric:** retain the unchanged expected behavior, PASS/FAIL/NOT RUN.

No numerical average can cancel an evidence or delivery failure. Preserve every
failure and exact request/response, attach rationale to each rating, and report
sample size. Independent architectural review and actual WebUI integration
remain separate gates even if the screening succeeds.
