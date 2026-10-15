# Task 3.9 — isolated fake HTTP transport

October 14, 2026. Started clean at published checkpoint
`6aa0ee581897bd345e7e143063d030b6dc181d01`, branch
`feature/brain-v0.2-experiments`. GitHub confirmed PR #12 draft and unmerged.
All Task 3.9 changes remain local and uncommitted.

**108 offline tests PASS, including 13 new HTTP tests and all 16 unchanged frozen
harness checks. Ruff lint/format PASS. GO for offline review; NO-GO for a live screen
with this implementation. No live endpoint can be selected.**

## Minimal implementation and boundary

`HttpFixtureHarness` subclasses the existing process controller. The only change
to `mock_harness.py` is a trusted class-level worker filename selector, defaulting
to its original worker. Public JSON and manifests cannot select the filename.
Existing process limits, single-flight guard, cancellation, stopped-batch behavior,
fixed public JSON and private reviewer handoff are reused, not reimplemented.
`boundary.py`, `gateway.py`, original worker and all prior tests are unchanged.

`http_fixture_worker.py` starts its own fake HTTP server on `127.0.0.1` with an
OS-assigned ephemeral port, then makes one HTTP POST to that owned listener.
There is no arbitrary endpoint, DNS name, live-mode switch, proxy configuration,
redirect following, retry, external model identifier or tool support. Its model
identifier is the nonexistent `moriq-offline-fixture`. A refusal fixture uses a
separately bound non-listening local socket; it does not probe another service.
The server and its thread are inside the disposable worker process. Cancellation
or deadline termination ends the fixture server along with the HTTP client.

This implements a deliberately narrow Ollama-shaped `/api/chat` contract:
`model`, `messages`, `stream: false`, CPU-only options, a 600-token option and
`keep_alive: 0`. These are serialized request fields tested against fake HTTP;
they are not evidence that a real provider enforces CPU, token or unload behavior.
The gate instruction is the system message. Question and evidence are serialized
as user data; source text cannot become transport configuration or a system role.

Only generation already permitted by the real gate launches the worker. Private
reviewer credentials, signing keys, audit state and attestation objects never enter
the worker. Source text and generated text use private bounded pipes. The parent
extracts actual citation IDs and sends the draft through the same citation and
post-generation evidence checks. False claims with valid IDs remain private, not
certified. There is no user-facing answer-release path.

## Validation and limits

The request body and HTTP response body are capped at 32 KiB. The existing process
protocol caps input/stdout at 64 KiB and stderr at 16 KiB. Fixture manifests retain
the existing hash, request-count, exact-request and mock-only configuration checks.
Request schemas reject extra configuration and malformed evidence fields.

The response requires HTTP 200, exactly one `application/json` content type, no
compression/transfer encoding, and an optional single bounded decimal content
length. Truncated declared bodies reject. Only a complete JSON object with the
fixture model, assistant message, `done: true` and `done_reason: stop` is accepted.
Duplicate keys, nonfinite constants, trailing objects, unknown fields, tool calls,
empty/non-string content, incomplete output and token-limit completion reject.
No citation repair or response repair occurs.

This is a strict subset, **not verified general Ollama compatibility**: real
Ollama responses may contain timestamps, duration/count telemetry, thinking fields
or other encodings that this parser rejects. Support must be specified and tested
offline before connecting a real transport; do not silently relax validation.
HTTP header parsing also has the Python standard-library limits, separate from
the 32 KiB body cap; this is not an OS memory quota.

The worker's two-second socket timeout is supplementary. The parent's monotonic
deadline remains authoritative across blocked headers, body reads, parsing and
pipe handling. Any failure stops the batch. Timeout is a result-acceptance bound
plus the existing bounded process/pipe cleanup allowance, not a hard real-time
OS guarantee. Tests inspect process exit and closed stdin/stdout/stderr. Cancellation
is accepted only while the worker is running, as in Task 3.8; it cannot retract a
draft already delivered to an authorized reviewer.

HTTP server logging is disabled; unexpected worker exceptions exit with a fixed
code without printing exception text or HTTP bodies. Native stderr contamination
still rejects at the parent. Parent logging/stdout/stderr captures and public JSON
checks contain no private sentinels. The trusted reviewer method returns inert
private JSON only after authorization. No transcripts are persisted by the harness.

## Threat model

Untrusted: questions, source text, model-shaped HTTP bodies, malformed protocol
fields, redirects, errors and streamed/partial data. Trusted: local operator,
manifest digest, controller/fixture code, Python runtime, reviewer mapping and
process-local audit/key storage. The worker has a minimal inherited environment,
no shell, private pipes and no production credentials.

The fixture server is owned locally, not an authenticated remote server. These
tests demonstrate parsing and boundary behavior, not server identity or TLS.
Loopback isolation does not protect against a malicious administrator or arbitrary
host code. The trusted Python class attribute is not an authorization boundary
against an attacker who can modify the host process. Process isolation is not a
sandbox for hostile executable code. Network access is restricted by construction
to the owned fixtures, not by an OS outbound firewall policy.

## Actual results

| Check | Result |
| --- | --- |
| Original source gate/lifecycle/mock harness tests | 80 PASS |
| New HTTP fixture tests | 13 PASS |
| V0.2 / V0.2.1 / original Brain | 4 / 3 / 8 PASS |
| Total | **108 PASS, no skips** |
| Original frozen H01–H16 | **16 PASS, criteria unchanged** |
| Ruff lint / format | PASS / PASS (31 Python files) |
| Prior experimental evidence | **67/67 hashes match** |

The 13 HTTP tests cover fixed request serialization/options and invalid input;
success with ignored proxy environment; source-less/mixed/injected requests with
zero workers; connection refusal/disconnect, 500/302 and stderr; malformed,
duplicate/truncated/oversized JSON; incomplete/tool/wrong-model responses; blocked
headers and slow bodies; cancellation/concurrency/cleanup/stopped batches;
preflight revoked/tampered attestations; citations/private authorization; forbidden
endpoint/live configuration; invalid HTTP framing/encoding; and revocation,
expiration and supersession during an in-flight delayed response.

The initial 11-test HTTP run passed; two additional focused tests were then added
before the full 108-test run. Initial formatting/complexity lint findings were
resolved without suppressions. No failing behavioral result was hidden. Raw test
output and hashes are saved separately in `http_evidence/`; original Task 3.5–3.8
reports, failures and hash manifests remain historical evidence and unchanged.
The saved Task 3.8 controller hash describes its old version; this report explicitly
records the new selector change and preserves the original bytes.

Reproduce from the repository root using the already installed Python and Ruff:

```text
python -m unittest discover -s moriq/brain/experimental/source_gate -p "test*.py" -v
python -m unittest discover -s moriq/brain/experimental/v02 -p "test*.py" -v
python -m unittest discover -s moriq/brain/experimental/v021 -p "test*.py" -v
python -m unittest discover -s moriq/brain/tests -p "test*.py" -v
ruff check moriq/brain/experimental/source_gate moriq/brain/tests moriq/brain/experimental/v02/test_experiment.py moriq/brain/experimental/v021/test_screen.py
ruff format --check moriq/brain/experimental/source_gate moriq/brain/tests moriq/brain/experimental/v02/test_experiment.py moriq/brain/experimental/v021/test_screen.py
```

Windows tests need writable temp storage and loopback socket permission. The
recorded run used the existing workspace temp folder. Fake HTTP is actual local
socket traffic, but **not a live provider or model test**. Test runtimes are not
inference latency or evidence of architectural correctness.

## Remaining gates and decision

- **P1 before real integration:** production identity, scoped reviewer access,
  protected durable audit/key storage and independent source review are absent.
  HMAC consistency is not evidence authenticity or expert certification.
- **P1 before a live screen:** no reviewed live endpoint adapter or complete real
  response schema exists. Exact endpoint/model/CPU/settings and approved requests
  must be frozen, tested with fake responses and independently reviewed. No prompt
  or public/source input may select those settings.
- **P2 before a live screen:** killing the worker would not prove a separately
  running provider has stopped. Specify idleness checks, RAM/concurrency policy,
  failure recovery and private output storage/access before any live execution.

**GO:** review this isolated offline implementation. **NO-GO:** execute a live screen
with it or deploy it. A later tiny screen needs a separately reviewed transport,
explicit approval of the exact manifest and endpoint, no source-required generation
without genuinely reviewed evidence, and separate scoring of delivery, correctness,
citations and latency. There is no approval to connect in this task.

No live Ollama/API call, model inference/download, Docker operation, credential
change, commit, push, PR update, merge, deployment or paid resource was used.
Full upstream application tests, real provider compatibility/cancellation and human
source verification were not performed.
