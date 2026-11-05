# Ready-to-copy continuation prompt
You are continuing MORIQ AI V1 from its preserved migration repository. Read CLAUDE.md, AGENTS.md and docs/moriq-project/DOCUMENTATION-INDEX.md, then current status, development history, architecture, security limitations and migration test results. Verify actual Git HEAD/branch/status and file hashes before editing. Do not assume local work is on GitHub or that all feature branches are integrated.

Preserve the ten historical working-byte changes, all five untracked offline_integration files, frozen evidence and authentic Studio assets. The last accepted local integration milestone is the 6.1B offline facade, on top of 6.1A; after a label-only test ID change backend.py/test_backend.py pass 57 cases, and the owner accepted [the closeout record](TASK-6.1B-CLOSEOUT.md) with its recorded limits. Earlier 56-pass/2-error runs remain evidence. Check for newer evidence before naming the next step.

Run relevant existing offline tests in isolated processes, record failures accurately, and inspect the recovered 6.1B implementation. Task 6.1B acceptance criteria are frozen in the closeout record; do not change them or the frozen test set without owner approval. For any later task, freeze acceptance criteria and obtain authorization before implementation. Do not regenerate or overwrite recovered work.

No live inference, real/confidential ingestion, production private viewing, automatic answer release, deployment, dependency upgrades, fixture edits or disabled-adapter activation. No commit/push/merge or remote changes without approval. Keep the approved dark Studio design and use the documented recovery process if versions conflict.

## Documentation publication qualification
Read [PUBLICATION-SCOPE.md](PUBLICATION-SCOPE.md): the first commit excludes studio-preview and offline_integration. Their setup/test instructions describe the local recovery workspace, not a fresh clone. Keep the actual recovered files; do not regenerate them from these documents. The initial documentation PR should target feature/knowledge-rag-v0, not develop, to avoid including unrelated unmerged history. CLAUDE.md matches an inherited ignore rule but has been tracked since the documentation commit; commit changes to it only with approval.

[Task 6.1B error analysis](TASK-6.1B-TEST-ERROR-ANALYSIS.md) establishes one oversized parameter-ID case with setup and teardown errors. That investigation made no application or frozen-test change. The owner later accepted 6.1B as an offline facade; see the [closeout record](TASK-6.1B-CLOSEOUT.md).
