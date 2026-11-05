# Claude handoff
MORIQ is an architectural intelligence platform on Open WebUI. V1 should connect its Studio, Brain, controlled knowledge and backend lifecycle. The current state is offline components plus a fixture UI, not an integrated deployed assistant.

Start at DOCUMENTATION-INDEX.md, CURRENT-PROJECT-STATUS.md, FULL-DEVELOPMENT-HISTORY.md, SYSTEM-ARCHITECTURE.md, SECURITY-AND-LIMITATIONS.md and MIGRATION-TEST-RESULTS.md. Inspect Git and current bytes yourself. Local code may be newer than GitHub: five offline_integration files are untracked; ten historical source files have intentional working-byte restorations. Studio lives in studio-preview and remains independently runnable. Do not infer all historical work is merged.

Canonical baseline is b78466029a751825c75424ff14d80e2bc82ee631 on a new uncommitted documentation branch. PR13 depends on PR12; PR11 remains separate. Historical source-gate commit is 21a03cc2af98cf8a0a0d6541ffdc1fbf35e07bfb and Brain checkpoint is 50cb6533f62cd2f28bcf7a236c5f2868fe05bb1f. Follow the branch inventory and recovery manifest for originals and other versions.

Last accepted local integration milestone: 6.1B offline facade, on top of the 6.1A contracts. Its backend/test files pass 57 cases after a label-only test ID change, and the owner accepted [the closeout record](TASK-6.1B-CLOSEOUT.md) with its recorded limits. Earlier saved runs with 56 passes and 2 errors remain evidence. Committing the local-only work and proposing Phase B each need separate owner approval. Do not regenerate 6.1A or replace 6.1B. Verify whether subsequent work has appeared before acting.

Use the isolated suite commands in TESTING-AND-VALIDATION. Keep source_gate import paths, synthetic clock controls, H15/runtime hashes and fixed public no-text/no-citation projections unchanged unless explicitly reviewed. The 6.1B facade is not a production endpoint. All live inference, real sources, automatic answer release and deployment remain gated.

Task 4 owner-led offline acceptance is narrower than independent V12 and production approval. Preserve original failed benchmarks and unsigned forms. Task 5 visual evidence does not establish spoken screen-reader, zoom or physical-device acceptance. Do not publish images, private archive contents or absolute machine paths. Commit, push, merge and remote mutation require explicit approval.

## Documentation publication qualification
Read [PUBLICATION-SCOPE.md](PUBLICATION-SCOPE.md): the first commit excludes studio-preview and offline_integration. Their setup/test instructions describe the local recovery workspace, not a fresh clone. Keep the actual recovered files; do not regenerate them from these documents. The initial documentation PR should target feature/knowledge-rag-v0, not develop, to avoid including unrelated unmerged history. CLAUDE.md matches an inherited ignore rule but has been tracked since the documentation commit; commit changes to it only with approval.

[Task 6.1B error analysis](TASK-6.1B-TEST-ERROR-ANALYSIS.md) establishes one oversized parameter-ID case with setup and teardown errors. That investigation made no application or frozen-test change. The owner later accepted 6.1B as an offline facade; see the [closeout record](TASK-6.1B-CLOSEOUT.md).
