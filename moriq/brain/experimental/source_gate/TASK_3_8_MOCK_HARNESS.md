# Task 3.8 — isolated mock-only harness

October 14, 2026. Branch `feature/brain-v0.2-experiments`; unchanged HEAD
`9f487f08faef3fe09418b259232bbbabc8c39d04`. All changes remain local/uncommitted.

**Mock-only implementation complete: 16/16 frozen acceptance checks PASS; 95
offline tests PASS. GO for independent review/checkpoint approval. NO-GO for
live inference now: no live transport exists or is authorized.**

## What changed

Three new Python files, no changes to the existing gate or boundary:

- `mock_harness.py`: validates an operator-supplied, hash-bound mock manifest;
  wraps the real `OfflinePrototype.public` method; supplies its generation
  callback; enforces one active request, limits, cancellation and stopped batches.
- `mock_worker.py`: deterministic fixed scenarios in a disposable child process.
  There is no Ollama/API client or arbitrary callable/code execution interface.
- `test_mock_harness.py`: 16 named acceptance methods plus two focused regressions
  for overdue parsing and invalid attestations rejected before worker launch.

Also added this report and `mock_evidence/` results/hashes. Previously untracked
Task 3.5–3.7 files remain present and unchanged. All 67 prior experimental hashes,
38 initial local additions and the frozen checklist/design bytes still match.

## Real boundary, fake generation

The harness calls the existing public adapter; it does not duplicate routing,
attestation or citation validation. Only an allowed generation callback launches
a worker. Source gaps make zero worker/provider calls. Reviewer operations use
`harness.reviewer`, the real test-authorized boundary owned by trusted host code;
public JSON cannot select reviewer operations or serialize its objects.

The worker returns exactly one JSON object with `done: true` and string `text`.
The parent derives identifiers only from actual ASCII [id] markers, without
repairing or inventing them, and returns `Draft` to the existing gate. The gate
validates citations and current attestations and holds valid drafts privately.
Even a false claim with a valid identifier stays private and is not scored factual.

## Process isolation and bounds

This is real subprocess isolation, not a thread timeout around model code.
`Popen` uses an absolute interpreter, fixed worker path, isolated Python mode,
unbuffered pipes, no shell, closed inherited handles and a minimal environment
containing only Windows system-directory variables when present. Credentials,
signing keys and registry objects are not passed in arguments, environment or
protocol input. Threads only drain pipes/send bounded input; the fake callback
runs in the child. On Windows the child window is hidden.

Limits: manifest <= 1 MiB; 1–16 cases; public/worker input <= 64 KiB; stdout <=
64 KiB; stderr <= 16 KiB. Deadline is finite and explicitly configured between
0.05 and 5 seconds for these mock fixtures, measured with the controller's
monotonic clock independently of blocked reads and worker output activity.
These are mock limits, not a chosen live-model token/time budget.

Any stderr, protocol contamination, duplicate keys, multiple replies, trailing
bytes, invalid schema/types, missing completion, oversized output, tool payload,
crash or exception fails closed. Raw pipe buffers and exceptions never become
public messages or ordinary application logs. The harness writes no logs and
persists no raw outputs. Tests inject print/logging/native `os.write` sentinels
in the worker and capture parent stdout/stderr/logging to check this boundary.

Timeout, accepted cancellation or generation/protocol failure stops the batch.
There is no retry, queue or reset API; a new trusted operator session requires a
new harness instance. Concurrent requests get fixed `busy` JSON without launching
another process. Subsequent requests to a stopped/exhausted batch get fixed
`stopped` JSON. Neither response contains worker data.

Cancellation is accepted only while the child is running; after it exits, cancel
returns false and is too late to retract a completed private result. Deadline
checks also reject a result that became overdue while parsing. Cleanup kills a
running child, waits for its exit (up to 2 seconds), joins each pipe thread (up to
1 second each), checks no thread remains alive and closes all pipes. The configured
deadline is therefore a result-acceptance deadline plus bounded cleanup allowance,
not a hard real-time OS scheduling guarantee. Tests inspect the actual child exit
status and closed pipes. OS process creation/termination failures or host suspension
remain platform limits; cleanup failure stops the batch and must be investigated.

The fixed worker does not spawn descendants. Its network entry points are disabled,
and tests use failing parent socket/HTTP spies. These are code-level no-network
guards and process/pipe isolation, not an OS sandbox for arbitrary hostile Python.
A terminated worker would not prove an external provider stopped; no such provider
is connected in this implementation.

## Acceptance results — original criteria unchanged

The frozen `task37_acceptance.json` is untouched. Results are recorded separately
in `mock_evidence/acceptance-results.json`, tied to its SHA-256 hash. Each criterion
has a named executable test, with additional existing-suite evidence where noted.

| Check | Result | Evidence exercised |
| --- | --- | --- |
| H01 | PASS | Parent socket/HTTP spies; worker network guards; no transport client |
| H02 | PASS | Mixed/paraphrased/company/compliance gaps; zero worker launches |
| H03 | PASS | Success, raw malformed replies, unknown fields, exceptions, crash-path sentinels |
| H04 | PASS | Python print/logging and native stdout/stderr, captured separately |
| H05 | PASS | Input/output size caps, duplicate/multiple/trailing JSON, missing fields, bad types |
| H06 | PASS | Partial/truncated replies, error after content, missing terminal completion, tools |
| H07 | PASS | Cancel blocked process, verify exit/pipes, stopped latch, no second launch |
| H08 | PASS | Silent blocked worker, endless slow output, delayed result, overdue parsing |
| H09 | PASS | Simultaneous requests; one launch; fixed busy response, no queue |
| H10 | PASS | Missing/wrong/author-only tokens before serialization; private authorized view |
| H11 | PASS | Revocation/expiry/supersession during worker; pre-launch tamper/replay/substitution; existing legacy tests |
| H12 | PASS | Missing/malformed/wrong IDs rejected; false claim with valid ID remains private |
| H13 | PASS | Hash/count/mode/model/endpoint/tools/options changes rejected before launch |
| H14 | PASS | Minimal child environment/protocol, no key/token in arguments, no raw export API |
| H15 | PASS | All prior 77 tests and hashes preserved; separate per-check results |
| H16 | PASS | Live/API/Ollama mode and endpoint changes rejected even with matching manifest hash |

These passes mean the criteria were exercised with deterministic fake subprocesses.
They do not certify real provider cancellation, network handling, model quality,
source authority or production access control. Existing source-gate integrity
tests supplement H11; they are not replaced by the process tests.

## Before/after verification and retained failure

Before Task 3.8, the prior reviewed code had 77 offline tests and no implemented
harness; its 16 harness criteria were NOT RUN. The first new 16-method run passed,
but deeper deadline testing exposed a gap: parsing a completed reply could cross
the deadline and still return a draft. The failing focused test is preserved in
`mock_evidence/overdue-parser-before-fix.json`. A final deadline check after parsing
fixes it; that same test now passes. Initial Ruff complexity findings were resolved
by separating pipe handling and fault fixtures into small functions, without
suppressing lint checks or modifying the acceptance criteria.

Final results: source gate **80 PASS** (62 existing + 18 new), V0.2 **4 PASS**,
V0.2.1 **3 PASS**, original Brain **8 PASS**: **95 PASS total, no skips**.
Ruff lint/format pass; 26 Python files checked for formatting on this run.
All generation is fake. Test elapsed times are process/test timings, not model
response latency. Denied requests are not counted as generated answers.

Reproduce using existing Python/Ruff, from the repository root:

```text
python -m unittest discover -s moriq/brain/experimental/source_gate -p "test*.py" -v
python -m unittest discover -s moriq/brain/experimental/v02 -v
python -m unittest discover -s moriq/brain/experimental/v021 -v
python -m unittest discover -s moriq/brain/tests -v
ruff check moriq/brain/experimental/source_gate moriq/brain/tests moriq/brain/experimental/v02/test_experiment.py moriq/brain/experimental/v021/test_screen.py
ruff format --check moriq/brain/experimental/source_gate moriq/brain/tests moriq/brain/experimental/v02/test_experiment.py moriq/brain/experimental/v021/test_screen.py
```

Windows Brain tests require writable temporary storage and asyncio loopback setup;
the run used a workspace temp directory and socket permission solely for that
event-loop initialization. Harness IPC uses OS pipes. No live model/API calls ran.

## Use and remaining risks

`MockHarness(manifest_json, expected_sha256, test_credentials)` is a trusted local
library interface. The manifest binds exact requests and one of the fixed fake
scenarios. Call `public()` for its next exact request; use the separately authorized
reviewer interface for inert private JSON. The tests provide complete runnable
examples. No HTTP endpoint, executable live-provider CLI, persistence or public
answer-release method was added.

Remaining risks:

- **P1 before production:** static test identities, shared reviewer scope and
  process-local audit/key storage are not production authorization or provenance.
- **P1 before live integration:** a future transport could introduce new stream,
  error/log or credential paths. It must be reviewed and pass equivalent sentinel
  tests; the historical screening script is not a safe drop-in public adapter.
- **P2 before live integration:** external inference may continue after a client
  worker is killed. Provider-idle checks, resource/concurrency policy and explicit
  stop/recovery instructions must be designed for the actual provider.
- Privileged host code can access private memory/change configuration. Bounded
  pipe buffers are not a cap on arbitrary hostile process memory or child trees.
  No architectural or legal accuracy is established by fake source fixtures.

**Decision:** GO for independent review and a proposed clean checkpoint of the
mock-only implementation. NO-GO for executing a small live screen now. All frozen
mock criteria pass, so a separately scoped live-transport proposal may now be
prepared; it needs exact endpoint/model/settings, private-output handling, resource
and cancellation controls, offline transport tests and explicit execution approval.
No live harness was built here.

Proposed checkpoint title: `Add isolated mock harness with frozen acceptance tests`.
Include the reviewed prior untracked source/tests/docs/evidence and these new files;
exclude scratch/temp files, credentials and generated models. Preserve historical
failures. Keep PR #12 draft and PR #11 unchanged. Nothing was staged, committed,
pushed, merged, deployed, downloaded or promoted; Docker/Open WebUI was not touched.
