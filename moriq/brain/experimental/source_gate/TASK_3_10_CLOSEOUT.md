# Task 3.10 — final offline review and Task 3 closeout

Reviewed from published parent `6aa0ee581897bd345e7e143063d030b6dc181d01` on
`feature/brain-v0.2-experiments`. This is an independent code-inspection pass by
the coding agent, not an independent human security audit or architectural certification.

## Review outcome

No new blocking defect was identified within the documented trusted-host,
operator-controlled, fake-HTTP threat model. No implementation/test criteria were
changed during this review. The proposed source change is confined to the existing
worker-file selector plus the new HTTP fixture subclass, worker and 13 tests.

| Area inspected | Finding and practical limit |
| --- | --- |
| SSRF / loopback | Client destination comes from the worker's newly bound 127.0.0.1 listener. No endpoint parameter, public worker path, proxy inheritance or live model configuration exists. This is construction-level restriction, not an OS firewall or hostile-host sandbox. |
| Redirects | Non-200 replies reject; http.client does not follow the fake 302 Location. |
| Bounds / malformed data | 32 KiB HTTP body bounds; existing bounded IPC; exact response schema, duplicate/nonfinite JSON, missing completion, tools and bad framing reject. Standard-library header bounds are separate; no global OS memory quota is claimed. |
| Deadline / cancellation | Parent monotonic acceptance deadline is independent of socket reads. Accepted cancellation kills/reaps the worker and closes pipes; failures stop the batch. Cleanup adds bounded waiting and is not hard real-time. Cancellation after worker exit cannot retract a draft. |
| Concurrency | Nonblocking single-flight guard rejects a concurrent submission without queueing. Fixture server and client live in the same disposable process. |
| Logs / public output | Worker errors suppress raw traces; stderr contamination rejects. Public response uses a fixed catalog. No raw reply, private source or exception text is copied into public JSON or ordinary logs. Trusted private host methods must not be exposed as public endpoints. |
| Source/reviewer boundary | Only the real gate's generation callback starts HTTP; no-source code/company queries remain zero-call. Attestation validation precedes generation and rechecks after it; private view rechecks freshness and authorizes before serialization. |

The fixture manifest is trusted operator input. Its constructor parses nested
fixture JSON permissively, but the actual worker reparses it with duplicate-key
and nonfinite rejection before any connection. This does not provide a public
source-approval bypass; malformed fixture input fails closed at execution.
Transport helpers are trusted Python functions, not independently authorized APIs.

## Fresh validation and publication review

- **108 tests PASS, no skips:** 93 source-gate tests (80 prior + 13 HTTP),
  4 V0.2, 3 V0.2.1, 8 original Brain.
- **16/16 frozen H01-H16 acceptance checks PASS**, unchanged criteria.
- Ruff lint and formatting PASS (32 Python files inspected by this run).
- **67 preserved evidence hashes match.** Historical evidence manifests match;
  Task 3.9's intentional controller change is documented separately from its old hash.
- Reviewed all 13 initial proposed files, including the archived controller and
  JSON evidence. No actual credentials, signing keys, private project documents,
  generated caches, model artifacts or unrelated files were found. Test tokens and
  source strings are synthetic. Historical evidence retains local tool paths.
- Narrow Git attributes preserve the new hashed source/report bytes across
  checkout platforms; prior evidence is not rewritten.

Fresh command outputs and the original file inventory are in `closeout_evidence/`.
Task 3.9's initial successful 11-test run and subsequent 108-test run remain intact;
earlier Tasks 3.5-3.8 failures remain preserved. Timing here is test/process timing,
not model latency. No live provider endpoint was contacted.

Remote branch was fetched and matched the local published parent before checkpoint
creation. PR #12 was draft and unmerged. GitHub CLI authentication was reported
invalid in this execution session; publication may require normal-user authentication.
The final commit SHA/push result is recorded in the external Task 3.10 closeout and
PR status update so this document does not require an amend to name its own commit.

## Task 3 readiness, separated

| Track | Status | Decision |
| --- | --- | --- |
| Offline source gate, private boundary, attestation lifecycle, mock process harness and fake HTTP | Implemented and passing reviewed offline tests | **GO for experimental Git checkpoint and further offline review** |
| Local deployment | Historical runtime verification exists; Docker/Open WebUI were deliberately untouched and not rechecked here | Preserve deployment; no new runtime-health or activation claim |
| Live-model reliability and latency | Earlier model screens were mixed/failed; this task supplies no new live evidence or accepted model | **NO-GO for live execution or model promotion** |
| Production identity, authorization and audit | Static test identity/shared reviewer scope and in-memory keys/audit only | **NO-GO for production use** |
| Architectural/code/company correctness | Synthetic tests do not verify authoritative sources, jurisdiction applicability or factual entailment | **NO-GO for certified compliance or automatic answer release** |

Task 3's offline infrastructure checkpoint can close; the broader goal of a
reliably validated live MORIQ assistant is **not complete**. Passing identifier
checks does not establish claim truth. The original V0.1 deployment is not altered.

## Unresolved risks by severity

- **P1 before production:** real identity, scoped private access, protected durable
  audit/key storage and independent qualified source verification are absent.
  Privileged host code can change private state; the model cannot certify evidence.
- **P1 before live connection:** there is no reviewed real-provider transport/schema.
  The current exact fixture response schema intentionally rejects many potential
  real Ollama fields. Any new endpoint/settings/response handling requires review
  and fake-response tests, not a switch that relaxes validation.
- **P2 before live connection:** external inference could continue after killing a
  client worker. Define idleness checks, resource/concurrency limits, stop/recovery
  procedure and private storage/access before authorizing a screen.

These are known readiness blockers, not newly reproduced offline boundary exploits.
No live inference approval is granted by this closeout. Any later screen needs an
explicitly approved tiny manifest, exact endpoint/model/settings, resource checks,
private drafts, and separate scoring of delivery, correctness, citations and latency.

Not run: live inference, full upstream application suite, production identity/security
integration, human source review or architectural certification. No Docker/Open WebUI
changes, deployment, model download, paid resources or PR merges.
