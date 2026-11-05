# Task 6.1B closeout record — accepted 2026-11-04

**Status: accepted by the owner on 2026-11-04 as an offline, in-process facade only (criterion A8).** This acceptance is limited by the findings below and is not independent review or production approval. Nothing described here has been committed. The integration source remains local-only and untracked; see [publication scope](PUBLICATION-SCOPE.md).

## Bounded scope
In scope: the offline, in-process facade in offline_integration/backend.py: `handle`, `tick`, `issue_session` and `revoke_session`, and the JSON operations `start`, `status` and `cancel`.

Out of scope: network listener, Studio connection, generation or live models, real identity, durable audit, restart recovery, a real clock policy, real or confidential sources, answer release and production readiness.

## Recorded decisions
- Label-only change to test_backend.py permitted; the size-limit coverage gap is a finding only, with no new or changed cases. The owner delegated these two rulings to an advisor and accepted the recommendations.
- The owner approved the acceptance set below, including the retroactive-freeze caveat; accepted the revocation behavior as a documented offline limitation; kept the other coverage gaps as findings for Phase B; and authorized the regression runs and documentation updates.

- The owner accepted this record on 2026-11-04, replying "yes" when asked whether they accepted it or wanted changes first. The same reply approved the documentation index link and the status-wording updates.

The earlier decisions authorized the work recorded here; only the last one is acceptance of the task.

## Frozen acceptance set
The frozen test set is B01–B19 in offline_integration/test_backend.py, 57 collected cases, SHA-256 `3ef1a0ce5c68e5b26dbbb269ec99e00b8090c2a8cc9110d408cd6d7c33002655`.

**Caveat:** this set was frozen after the code and tests already existed. It records what the owner accepts as the boundary of this task. It does not show that the tests were designed independently of the implementation.

|ID|Criterion|Status at preparation|
|---|---|---|
|A1|B01–B19 frozen as above|Met by owner approval|
|A2|Backend 57 and contracts 66 pass in separate processes|Met|
|A3|Knowledge 116, preflight 53 and lifecycle 95 pass in separate processes|Met|
|A4|The guarantees below hold in code and tests|Met by the author's code reading and passing tests; not independently reviewed|
|A5|Findings and failed attempts recorded|Met by this record|
|A6|Documentation updated without rewriting dated evidence|Met; dated records keep their wording, as noted below|
|A7|Integrity checks show no unintended changes|Met at preparation; recheck before any commit|
|A8|Owner accepts this record; any commit is a separate decision|**Met: accepted 2026-11-04; no commit made**|

|Guarantee|Tests|
|---|---|
|Malformed input and unsupported operations rejected|B02, B07|
|Version handling|B03|
|Clients cannot claim authority; tickets are host-issued|B04, B17|
|Other identities denied|B05|
|Replay and duplicates|B06|
|Cancellation, ordering and concurrent isolation|B08, B09, B10|
|Failures sanitized|B11, B13|
|Clock disagreement denied|B12|
|Unapproved or revoked sources denied|B14, B15|
|Source gap|B16|
|Unpinned requests read nothing|B18|
|Generation stays disabled|B19|
|No text, citations or release in public output|`check()` helper, used by almost every test|
|No network, provider or ingestion calls|Autouse traps, checked at teardown|

## Test results
Fresh runs on 2026-11-04 used Python 3.12.14 and pytest 9.0.0, each selection in its own process, with bytecode and cache writes disabled and temporary output outside the repository. Methods are listed per suite and must not be summed with subtests or acceptance IDs. No subtests were reported in the two offline_integration runs.

|Selection|Result|
|---|---|
|offline_integration/test_backend.py, before the label change|57 collected; 56 passed, 2 errors (retained failed attempt)|
|offline_integration/test_backend.py, after the label change|57 collected; 57 passed|
|offline_integration/test_contracts.py|66 passed|
|moriq/knowledge|116 passed|
|moriq/brain/experimental/source_gate/test_knowledge_preflight.py|53 passed|
|moriq/brain/experimental/source_gate/test_private_draft_lifecycle.py|95 passed|

The earlier saved runs with 56 passes and 2 errors remain valid evidence of that state. The later pass does not erase them.

Not run for this closeout: pilot, frozen evaluation, security and Brain suites, because no shared code changed. Their results are not fresh.

**Environment limitation:** this runtime has no pytest of its own. An existing pytest 9.0.0 from another Python installation's site-packages was exposed through PYTHONPATH after the repository and source_gate paths, as in the historical launcher. Nothing was installed. This setup is not reproducible on another machine; a reproducible environment needs a separate, approved task.

## The change
One line in offline_integration/test_backend.py:

```diff
-@pytest.mark.parametrize('payload', [b'', b'{', b'[]', b'null', b'\xff', b'x' * 32769,
+@pytest.mark.parametrize('payload', [b'', b'{', b'[]', b'null', b'\xff', pytest.param(b'x' * 32769, id='oversized'),
```

The payload, assertions, fixtures and other nine IDs are unchanged. backend.py and contracts.py were not changed. The oversized case reached its test body and passed for the first time.

## Findings, not fixed
|#|Finding|Disposition|
|---|---|---|
|F1|backend.py checks the 32768-byte limit before JSON parsing, but the oversized case cannot prove the limit works. `b'x' * 32769` is also invalid JSON, so without the check it would still return `invalid_request`. A `resource_limit` code exists but is not used here. **A pass does not prove the limit works.**|Finding only, by ruling|
|F2|The acceptance set was frozen after implementation.|Caveat above|
|F3|The README had no 6.1B section, and this byte decoder had no separate contract.|README section added; no separate contract written|
|F4|After revocation, `tick` returns `source_reference_denied` and the job stays non-terminal until cancelled. It cannot advance and it does not end by itself. B15 asserts this.|Accepted offline limitation|
|F5|The 32 accepted IDs are never evicted, so the backend returns `resource_limit` until restart.|Accepted offline limitation|
|F6|Nesting is tested at 2,000 `[`, while the size limit allows 32,768 bytes. The larger depth is untested and may depend on the Python version.|Phase B|
|F7|test_backend.py has no case for non-bytes payloads, lone surrogates or more than 16 sources. Contract tests cover the source limit at contract level.|Phase B|
|F8|The 16-session cap: `test_C19_capacity` covers it at contract level.|Resolved; no backend-level case|

## Corrections to earlier records
The dated records stay as written; these corrections apply on top of them.

- TASK-6.1B-TEST-ERROR-ANALYSIS.md and the private handoff cite test_backend.py lines 101–103. The parametrize block was at lines 102–104, and line 101 is blank. The file hash matched the recorded hash and the file was LF-only, so the citation was wrong, not the file. How the error arose is unresolved.
- "Ten LF/CRLF-only changes" is inaccurate. Only three tracked files differ from HEAD, LF to CRLF: source_gate/README.md, source_gate/validation.json and v021/README.md. The other seven are byte-identical to HEAD. They probably show as modified because the Git index caches an older file size; this is inferred from the sizes and was not tested. The index was not refreshed.

## What this does not establish
This record does not establish production readiness, an HTTP service, real identity or audit, Studio integration or independent review. The author reviewed the code; that is not an independent review. Original Task 4 V12 independent review remains unmet.

## Open before any commit
- Remote state and PR #14 were read on 2026-11-04: PR #14 was an open draft, its head matched the local HEAD, and no CI checks were reported. Recheck before any push.
- All five integration files are LF, but no attribute covers them and `core.autocrlf=true` is set locally, so a later checkout could convert them to CRLF and break recorded hashes. If a commit is approved, add an exact `/offline_integration/* text eol=lf` rule with it.
- Commit with exact paths only, excluding the ten historical files and Studio. The target branch is undecided.
- Dated records keep their wording: MIGRATION-TEST-RESULTS.md, TASK-6.1B-TEST-ERROR-ANALYSIS.md, MIGRATION-VERIFICATION-REPORT.md, PUBLICATION-SCOPE.md and MORIQ-CHANGELOG.md. This record takes precedence for 6.1B status. CLAUDE.md matches an inherited ignore rule but has been tracked since the documentation commit.

Run logs, JUnit XML, hashes and the pre-change test file are retained in the private review package, outside the repository.
