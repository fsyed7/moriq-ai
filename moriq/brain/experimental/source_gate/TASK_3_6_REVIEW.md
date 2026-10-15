# Task 3.6 — offline review of the uncommitted Task 3.5 prototype

What this change does: Task 3.5 adds fixed public JSON responses, a private
test-authenticated reviewer interface and an in-memory attestation lifecycle.
This review adds six offline tests and preserves one genuine failing integrity
regression. It does not change the implementation or existing local work.

## Scope and evidence

Reviewed local branch `feature/brain-v0.2-experiments`, HEAD
`9f487f08faef3fe09418b259232bbbabc8c39d04`, October 14, 2026.
All Task 3.5 files were untracked additions, so ordinary `git diff` and the index
diff were empty. The full 12-file addition set was snapshotted and an additive
patch saved before review. The actual boundary, gateway, callers, lifecycle tests,
report, README, evidence manifests and historical `v021/screen.py` were inspected.

Assumed scope: one trusted Python process, small offline batches, test identities,
with threaded lifecycle changes supported. This is a fresh code-focused review
and new test set by Codex, not an external security audit or architectural expert
certification. No live GitHub, provider or production state was queried.

## Must fix before the small screen

1. **P2 — signed records can be substituted between registry IDs**
   (`boundary.py:87`, `boundary.py:97`).
   - **What this is:** HMAC authenticates record contents, but not the dictionary
     key identifying that attestation. Audit validation compares only its version.
   - **Problem:** Create two independently approved records for the same exact
     question/source ID, with different source text. Both have version 2. Copy
     the second stored record/seal pair to the first registry key. A request for
     the first key accepts the second evidence and invokes generation once.
     No signature, audit event or version was forged. The new test expects an
     error and zero calls; both assertions fail.
   - **Fix proposed:** Include the registry ID in the HMAC input and pass that ID
     consistently from `_save` and `_load`. Keep the version check. Retain this
     test and the existing old-version replay regression unchanged.
   - **If skipped:** Accidental or malicious storage substitution can silently
     change which approved record a reference resolves to. This matters within
     the same injected storage-corruption surface the existing tampering tests
     already exercise.

This is not a demonstrated remote exploit, forged approval, resurrection of a
revoked record or public model-output leak. The test deliberately mutates the
internal store to simulate corruption; public JSON cannot perform that mutation.
Both records were individually approved. Severity reflects broken identity
binding, not a claim that all authorization is bypassed.

No implementation fixes were made during this review. The current failure remains
visible and is not skipped or marked expected-failure. Task 3.5 bytes are preserved.

## Boundary, authorization and lifecycle assessment

- Public JSON has only fixed `status` and `message` strings. New tests confirm
  arbitrary internal result text and unknown statuses are not echoed. Mock
  generation emits no stdout/stderr unless the supplied callback itself does so.
- Private authorization runs before draft serialization. Missing credentials,
  author-only credentials, malformed tokens and forged role dictionaries cannot
  trigger the serializer. This verifies test-role checks, not real identity.
- Independent approval, exact-question checks, fictional-source rejection,
  expiry, revocation, supersession and same-ID stale replay tests still pass.
  Threaded revocation/expiry/supersession discards generated drafts, and private
  viewing removes drafts whose evidence is no longer current.
- Record and audit operations use a shared lock; generation is outside it.
  A revocation cannot cancel work already started. Date expiry is inclusive and
  lazy, not a timer or a lease. In-process snapshots are not durable transactions.
- Audit events are frozen objects in a trusted mutable list. The version check
  catches replay only while that history remains intact. Audit history is not
  independently authenticated, persistent or protected from a privileged host.
  Those limits were already documented; this review does not relabel them as
  newly discovered defects. Test tokens are static and all reviewers share access.
- Fixed public exception responses protect this method's output. Authorized
  private methods can raise exceptions to their trusted caller; any future
  transport must keep its error/debug output separate from public responses.

No additional public JSON disclosure defect was reproduced under the documented
trusted-host assumptions. This does not prove that every future integration is safe.

## Proposed provider harness assessment

Task 3.5 proposes a harness but supplies no implementation. Therefore transport,
streaming, log paths, cancellation and provider-error behavior are **NOT VERIFIED**.
The added characterization test deliberately supplies a callback that prints a
private marker: the JSON remains clean, but the marker appears on stdout. This
is the documented trusted-callback limitation, not another failed test or a
current public endpoint disclosure. Publicly forwarding that stdout would leak it.

The historical `v021/screen.py` is not a safe drop-in boundary adapter. It retains
raw answers/thinking in a caller-selected output file (line 201), copies provider
exception text into `record['error']` (line 158), and includes that error in console
summaries. That was experimental evidence collection, not authenticated reviewer
storage. No historical file was executed or changed. Never expose its output file,
console stream or provider stream as the new public response.

## Actual validation

| Check | Result |
| --- | --- |
| Existing Task 3.3–3.5 test methods | 50 PASS |
| New Task 3.6 methods | 5 PASS, 1 FAIL |
| Combined suite | 56 methods: 55 PASS, 1 FAIL; 2 failed subtest assertions |
| Ruff check, entire source_gate directory | PASS |
| Ruff format --check, entire source_gate directory | PASS (16 Python files) |
| Prior tracked experimental byte hashes | 67/67 unchanged |
| Initial uncommitted Task 3.5 file hashes | 12/12 unchanged |

All generation was mocked. The failure includes exactly one mock call carrying
the substituted evidence; it is not a real provider call. No inference latency,
architectural correctness or human source verification was measured. Existing
tests passing is not proof that supplied attestations are true.

Reproduce with the existing local Python and Ruff:

```text
python -m unittest discover -s moriq/brain/experimental/source_gate -p "test*.py" -v
ruff check moriq/brain/experimental/source_gate
ruff format --check moriq/brain/experimental/source_gate
```

The unittest command currently exits 1 intentionally because the reproduced defect
remains unfixed; do not describe this checkpoint as a green validation run.

## Precise go/no-go checklist

**NO-GO for a live screen now. GO for reviewing the saved patch and fixing finding 1.**

- [ ] Bind registry identity into the signed record; all 56 current tests must pass
  without weakening the substitution or same-ID replay assertions.
- [ ] Implement and inspect an isolated provider callback; only `public()` fixed
  JSON may reach public output. No streamed tokens, raw errors, exception traces,
  evidence, private view JSON, debug logs or provider stdout may share that path.
- [ ] Offline integration tests must inject sentinel text into answer chunks,
  partial output, errors and logs, including cancellation/serialization failures,
  and verify it is absent from every public output sink. Test the actual harness.
- [ ] Freeze a tiny manifest before approval. Suggested first scope: two general
  education requests plus two no-source compliance/company requests. Only the
  two education requests may invoke the model; all drafts stay private. No real
  code or company source is verified, and this adapter disables fictional exercise
  inference, so do not fabricate attestations to force those paths.
- [ ] Specify exact installed model/settings, CPU-only operation, one loaded model
  and one in-flight request, request/token/time caps, RAM/competition checks and
  stop-on-error behavior. Cancellation must not be mistaken for an idle provider.
- [ ] Define a non-public operator-only results location and trusted test reviewer
  access; keep model text inert and separate from public status reporting.
- [ ] Obtain explicit approval for that exact small manifest and harness. Preserve
  every output/failure and separately score delivery, factual correctness,
  unsupported claims, citations and latency. No automatic answer release.

Real-source tests additionally need qualified independent provenance/applicability
verification. A synthetic approval record or valid citation marker is not a substitute.
Production identity, tenant isolation, durable audit/key storage, anti-rollback
persistence and deployment readiness are separate gates, not passed by this work.

## Proposed commit and draft PR update — approval required

Proposed checkpoint commit title:
`Add offline attestation boundary and document adversarial review findings`

Scope: the untouched Task 3.5 additions, this review, six new tests and their saved
validation evidence. No tracked production or prior experimental files change.
The checkpoint deliberately records the known failing regression; it is suitable
only as a draft review checkpoint, not an accepted implementation. Prefer fixing
finding 1 and rerunning validation before approving a green implementation commit.

The proposed PR #12 update must state **55 PASS / 1 FAIL**, the registry-ID binding
defect, fixed public JSON contract, mocked-only evidence and NO-GO checklist. Its
ready-to-review text is saved separately. Keep PR #12 draft and PR #11 unchanged.
No staging, commit, push, remote PR update, merge or credential change occurred.

Verdict: fix finding 1 and verify the actual isolated harness before live inference.
Not checked: live providers, production authentication, human source authority,
architectural accuracy, running deployment or full upstream application tests.
