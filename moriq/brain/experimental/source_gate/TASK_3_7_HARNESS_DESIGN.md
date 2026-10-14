# Task 3.7 — reviewed boundary and minimal isolated harness design

What this change does: the current prototype keeps generated drafts out of public
JSON and requires test-authorized reviewers and identity-bound attestations.
This task independently traces that implementation and specifies a small harness;
it does not implement or connect one.

**Verdict: GO to implement the harness offline against fake transports. NO-GO for
live inference, deployment or production use.** Git publication still needs approval.

## Review scope and findings

Reviewed October 14, 2026 on `feature/brain-v0.2-experiments`, HEAD
`9f487f08faef3fe09418b259232bbbabc8c39d04`. The 29 uncommitted additions from
Tasks 3.5–3.6.1 were inventoried, hashed and captured as a full additive patch;
ordinary Git diff is empty because those files are untracked. Reviewed actual
`boundary.py`, `gateway.py`, signing/load/save callers, public/private flows,
tests and the historical screening script, not just prior conclusions.

No new implementation defect was reproduced within the stated scope: one trusted
Python process, small operator-controlled batches, untrusted JSON/source/model
text, and simulated record-store corruption while keys/audit remain trusted.
No additional regression test was justified. This is a new Codex review pass,
not an independent human audit or architectural certification.

Verified by code trace and the rerun suites:

- `_seal(key, record)` requires a canonical key matching the embedded registry ID;
  both identity and record fields enter the v2 HMAC payload. Transplanting equal-
  version records, rewriting their IDs and legacy signatures all reject. There
  is no legacy fallback, automatic resigning or approval migration.
- The audit version check still rejects stale signed approvals. Terminal states
  stay terminal. Generation and private viewing recheck current evidence; race
  tests cover expiry, revocation and supersession during generation.
- Self-approval uses resolved identity, not token spelling. Private viewing
  authorizes before serialization. Public output uses a fixed JSON catalog and
  never copies gateway text, raw exceptions, source objects or private drafts.
- A valid citation attached to a false claim remains private; the check is source
  identifier validation, not claim accuracy. Source-less compliance questions
  remain zero-call gaps. General education is allowed only by the bounded grammar.

### Remaining issues by severity — integration gates, not newly discovered bugs

1. **P1 if integrated incorrectly: callback output bypasses JSON isolation.**
   What: a supplied callback can print, log or stream private text. The existing
   characterization test demonstrates stdout exposure while public JSON stays
   clean. Problem: sharing that stream with public users leaks unverified prose.
   Required harness control: isolate worker output at the OS pipe boundary and
   never forward it to the public channel. If skipped: fixed JSON alone cannot
   prevent disclosure. No current public endpoint leak is claimed.

2. **P2 before live use: cancellation, time and concurrency are not enforced by
   the gateway.** What: it calls a synchronous trusted callback outside its state
   lock. Problem: that callback can hang or be invoked by simultaneous requests;
   closing its connection does not prove the provider stopped inference.
   Required harness control: one non-queued request, external deadline and a
   stop-latched state after abort/uncertain completion. If skipped: overlapping
   inference and a stalled queue can repeat earlier performance failures.

3. **P1 for production (explicitly outside this experiment): test identity and
   in-memory audit are not a security service.** What: static tokens, shared
   reviewer access and process-local keys/history. Problem: a privileged host
   can alter both state and audit, and attestations merely record assertions.
   Required production control: real identity, scoped access, durable protected
   state and qualified source review. If skipped: no production authorization or
   source-authority guarantee is justified. These are documented limits, not
   reasons to block offline harness development.

## Minimal design: one controller, one disposable worker, existing gate

No web server, Open WebUI plugin, prompt promotion, model installer, database or
automatic answer-release API. Keep `OfflinePrototype` as the gate. A separate
operator-only harness owns it and supplies one constrained generation callback.
Build and test a fake-transport worker first; live transport remains disabled.

```text
Frozen request manifest -> controller -> OfflinePrototype.public(request)
                                       -> generation callback (only if gate permits)
                                          -> disposable worker / bounded private pipes
                                          -> validated Draft back to gate
                                       -> fixed public JSON only
Test-authorized reviewer -> view(token) -> private operator-only channel
```

**Controller:** validates a local manifest digest and exact permitted request count,
owns the test credentials/attestations and a nonblocking single-flight guard.
A concurrent request gets a fixed busy status without launching or queuing work.
Only the controller writes the public channel, exclusively from the existing
public response catalog (plus a fixed busy response at the harness boundary).
Credentials, signing keys and registry objects never enter the worker environment
or command line. Request content travels over a private pipe, not shell arguments.
Use structured process arguments, no shell. No model text chooses commands or URLs.

**Worker:** trusted minimal code in a disposable child process, with OS-level stdout
and stderr captured separately and never inherited by the public console. No
Python-only global `redirect_stdout` as the isolation mechanism: native writes and
concurrent threads can escape it. Drain both pipes with size limits to avoid deadlock.
Its stdout is one bounded JSON protocol reply, not a user output stream. Unexpected
prints, multiple replies, trailing bytes, tool requests or malformed schemas reject
the whole reply. Stderr is untrusted diagnostic data; do not echo it on any error.
Do not execute model output or render HTML/Markdown from it.

**Transport seam:** injectable fake client for offline tests; no socket calls when
in fake mode. A future live client may only call an explicitly approved fixed
loopback endpoint/model, without redirects, proxy inheritance, tools or dynamic
URLs. Do not connect that implementation until separately authorized. Use buffered,
non-streaming public behavior: no token can reach the public channel early. If a
provider streams internally, assemble it only inside the worker and require a valid
terminal completion. Partial, truncated, oversized, tool-bearing or failed output
does not become a Draft. Citation IDs must come from the actual emitted markers;
never fabricate, repair or declare an expected ID merely to pass validation.

**Limits to freeze before any live approval:** suggested first batch is four
independent requests: two ordinary education questions and two source-less
company/compliance questions. Only two may invoke generation. No invented approvals
or real-source fixtures. Proposed bounds: one in-flight request; 64 KiB input;
64 KiB stdout and 16 KiB stderr per worker; 600 generated tokens; 30-second silent
read and 120-second monotonic total deadline. These are proposed conservative
screen limits, not a latency promise or a live authorization. The final manifest
must name the exact installed model/settings, CPU-only options and resource checks.

**Timeout/cancel:** the controller owns the deadline independently of blocked reads
and provider token arrivals. Cancel or deadline closes private pipes, terminates
and joins the worker, discards partial output and latches the batch stopped. Do not
start another request or retry automatically. A dead worker/closed socket does not
mean the external provider is idle; require an operator check before a new batch.
After machine suspension, an overdue worker result must also be discarded.

**Private handling:** initially keep valid drafts only in existing in-memory storage,
accessible through reviewer authorization. No public route to `view`, raw IPC or
debug objects. Do not persist raw worker output/errors by default. If a later
approved evaluation needs transcripts, separately specify an operator-only directory
and verify OS access restrictions; lack of that verification blocks raw exports.
Public logs have only allowlisted event codes/counts. Do not log prompts, credentials,
source text, paths from errors, model replies or exception repr/tracebacks publicly.
The worker's error detail is never a public status message.

The gate continues to check citations and attestation freshness after generation;
the harness must not write directly into the private draft store. Revoked evidence
cannot make a completed stale result viewable. Previously received private data
cannot be remotely erased from an authorized reviewer's memory or screen.

## Threat model and limits

Assets: private drafts/evidence, test credentials, signing keys, attestation identity,
public-output integrity and availability of this bounded batch. Untrusted inputs:
public JSON, source text, model replies, transport errors, stdout/stderr, partial
streams and filesystem/network error messages. Assumed trusted: controller code,
worker code, operator manifest/OS account, process key and audit history.

Defend against prompt/source injection changing routing, forged metadata/citations,
record substitution/replay, output/error leakage, oversized/malformed protocol data,
concurrent requests and delayed responses following revocation/cancellation. Model
text has no tools, executable authority or ability to configure the provider.

Not a sandbox against arbitrary hostile Python/OS administrator code, not a
multi-tenant service, not durable or crash-recoverable, and not proof of factual or
legal accuracy. A subprocess with private pipes isolates accidental output paths;
it is not an OS security sandbox. Real identity/source verification is absent.

## Frozen acceptance checklist

`task37_acceptance.json` is version 1, frozen and hashed before implementation.
Every row is currently **NOT RUN against a harness**, because none exists. Existing
unit-test coverage is separate. Implement each row with fake provider/worker
fixtures, including native `os.write` sentinels, and retain raw test results.
Changes to criteria require a new version and preserved old hash, not editing this
baseline to make an implementation pass. Only all-PASS plus review can permit a
request for separate live-screen approval.

## Validation and proposed Git checkpoint

Rerun results: source gate 62 PASS, V0.2 4 PASS, V0.2.1 3 PASS, original Brain 8 PASS:
**77 offline tests PASS, no skips.** Ruff lint passes; formatting passes for 22 Python
files. The source-gate count is not 77; totals include the other suites. Windows
asyncio uses permitted loopback initialization; no provider endpoint was called.

Preservation: all 67 prior tracked experimental hashes, all 29 initial uncommitted
files, and all 72 historical output files under the prior task directories remain
byte-identical. No existing code/test/report/evidence file was edited. Only this
design/checklist and review evidence are added. No duplicate tests were added just
to increase counts. Test output contains mocks, not live provider evidence.

Proposed single clean checkpoint after approval:
`Add reviewed offline attestation boundary and freeze isolated harness gates`
Scope: existing Task 3.5/3.6/3.6.1 additions plus Task 3.7 design, checklist and
validation evidence, all under `moriq/brain/experimental/source_gate/`. Include
historical failed evidence unchanged, with the later successful fix clearly dated.
Exclude scratch files, environment files, credentials, caches and generated models.
Before committing/pushing, recheck the index, branch/head and remote PR #12 status;
keep it draft targeting develop and leave PR #11 unchanged. No staging or remote
changes occurred here. Current approval is for review/design only.

Verdict: GO for offline harness implementation under this design; NO-GO for live
connection until its frozen checks pass and the exact small screen is authorized.
Not checked: live transport, cancellation of real inference, production identity,
human source verification, architectural accuracy or deployment runtime.
