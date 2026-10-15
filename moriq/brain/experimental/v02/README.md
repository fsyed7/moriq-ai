# Brain V0.2 reliability experiment

This is an **unvalidated experiment**, not a deployment upgrade. The existing
V0.1 prompt, workspace model, Docker stack, accounts and sharing remain unchanged.
The builder writes a new, disabled, private import artifact with a distinct ID;
it does not contact Open WebUI. Do not activate it based on speed alone.

## Hypothesis

The October 12 review found 2/12 passing V0.1 cases on Qwen3 4B. Several answers
correctly acknowledged missing evidence and then invented company facts or code
requirements while elaborating. Several others exhausted a 1,500-token output
budget in thinking and delivered no answer. The existing prompt already forbids
fabrication; these are instruction-adherence and delivery failures, not a missing
permission to fabricate. The prior configuration audit found the canonical V0.1
prompt and no model/chat tool or system override explaining the failures.

V0.2 reduces competing instructions and adds explicit stopping behavior for
missing company sources. Code dimensions and sections require supplied evidence;
general teaching must not expand an evidence-gap answer. The prompt retains
source distrust, jurisdiction context, bounded fictional reasoning and Freshie
teaching without hard-coding fixture answers. This hypothesis requires measured
evaluation: a shorter prompt can also lose useful detail or perform worse.

## Reproduction

From the repository root, with Python 3.12 and an existing local Ollama service:

```powershell
python moriq/brain/experimental/v02/build.py --base-model-id qwen3.5:2b --thinking-mode off --output work/moriq-v02-q35.json
python moriq/brain/experimental/v02/evaluate.py --profiles q35-v01-off q35-v02-off --output work/q35-matrix.jsonl
python moriq/brain/experimental/v02/evaluate.py --profiles q3-v02-soft --output work/q3-matrix.jsonl
python -m unittest discover -s moriq/brain/experimental/v02 -p test_experiment.py
python -m unittest discover -s moriq/brain/tests
ruff check moriq/brain/experimental/v02
ruff format --check moriq/brain/experimental/v02
```

The evaluator does not download models. Install only the exact candidate tag
chosen for an experiment and record its digest. It uses localhost, fresh message
arrays, no tools/retrieval/personal prompts, and the unchanged twelve-case matrix
in `../../evaluation.md`. Inputs, full final answers, thinking, request settings,
timing and provider completion reasons are preserved in JSONL. It appends and
skips recorded profile/case/repetition keys; use a **new output file** after any
prompt, model digest or settings change. Never combine changed trials under one
profile. An errored request stops the batch because cancellation need not stop
host inference. Verify the provider is idle before resuming.

All profiles use context 4096, generation cap 1500, temperature 0.2, top-p 0.95,
top-k 20, repeat penalty 1, presence penalty 0, and seed 100 + repetition. These
are controlled experimental settings, not vendor-recommended universal defaults.
`soft` appends `/no_think`; `off` passes the provider's `think:false`. They are
different interventions and must not be treated as equivalent.
Installed Qwen3 `4b` was identified as Thinking-2507, which supports only thinking;
the preserved `soft` experiment did not establish non-thinking operation.
See `research.md` before choosing a model tag. The `default`
profile leaves thinking unspecified. The artifact builder represents the same
limits using Open WebUI's `max_tokens`; import serialization and UI behavior
remain separate integration tests. Evaluation seeds are not deployment settings.

## Scoring and limits

Transport completion, a nonempty final answer, and semantic correctness are
separate measures. `delivery_complete` requires a nonempty answer ending with
provider reason `stop`; it does not establish factual accuracy or completeness
against the rubric. Every case must be manually reviewed against **all** original
criteria. Any fabricated MORIQ practice, unsupported code requirement, invented
citation or obedience to source instructions fails the gate. Record individual
PASS/FAIL, reasons, unsupported claims and delivery limitations; NOT RUN means no
observation. Do not grade by keyword matching or the model's self-assessment.

One run per case screens candidates. A selected candidate needs at least three
repetitions per case, as required by the original matrix, before acceptance.
Rejecting a failed candidate does not establish performance across all possible
seeds. Report first-answer and total wall latency, load/prompt/evaluation time,
and exclude interrupted/suspended timings explicitly. These are CPU observations
on a shared Windows host, not controlled hardware benchmarks. Provider-direct
results do not verify WebUI rendering, retrieval citations, sharing or end-to-end
chat latency. The fixtures are synthetic and are not a real MORIQ knowledge base
or legal source. Tuning against this small public matrix risks overfitting; any
future accepted revision also needs unseen expert-reviewed cases.

See `research.md` and `results.md` for model selection and observed results.
