# Claude handoff
MORIQ is an architectural intelligence platform on Open WebUI. V1 should connect its Studio, Brain, controlled knowledge and backend lifecycle. The current state is offline components plus a fixture UI, not an integrated deployed assistant.

Start at DOCUMENTATION-INDEX.md, CURRENT-PROJECT-STATUS.md, FULL-DEVELOPMENT-HISTORY.md, SYSTEM-ARCHITECTURE.md, SECURITY-AND-LIMITATIONS.md and MIGRATION-TEST-RESULTS.md. Inspect Git and current bytes yourself. Local code may be newer than GitHub: five offline_integration files are untracked; ten historical source files have intentional working-byte restorations. Studio lives in studio-preview and remains independently runnable. Do not infer all historical work is merged.

Canonical baseline is b78466029a751825c75424ff14d80e2bc82ee631 on a new uncommitted documentation branch. PR13 depends on PR12; PR11 remains separate. Historical source-gate commit is 21a03cc2af98cf8a0a0d6541ffdc1fbf35e07bfb and Brain checkpoint is 50cb6533f62cd2f28bcf7a236c5f2868fe05bb1f. Follow the branch inventory and recovery manifest for originals and other versions.

Last completed local integration milestone: 6.1A offline contracts. Newer 6.1B backend/test files exist but saved testing ended at 56 passes and 2 errors with no completed closeout. The next safe task is a bounded review and completion proposal for this recovered 6.1B, not regeneration of 6.1A or blind replacement of 6.1B. Verify whether subsequent work has appeared, reproduce the errors, freeze acceptance, then request implementation authorization.

Use the isolated suite commands in TESTING-AND-VALIDATION. Keep source_gate import paths, synthetic clock controls, H15/runtime hashes and fixed public no-text/no-citation projections unchanged unless explicitly reviewed. The incomplete facade is not a production endpoint. All live inference, real sources, automatic answer release and deployment remain gated.

Task 4 owner-led offline acceptance is narrower than independent V12 and production approval. Preserve original failed benchmarks and unsigned forms. Task 5 visual evidence does not establish spoken screen-reader, zoom or physical-device acceptance. Do not publish images, private archive contents or absolute machine paths. Commit, push, merge and remote mutation require explicit approval.

## Documentation publication qualification
Read [PUBLICATION-SCOPE.md](PUBLICATION-SCOPE.md): the first commit excludes studio-preview and offline_integration. Their setup/test instructions describe the local recovery workspace, not a fresh clone. Keep the actual recovered files; do not regenerate them from these documents. The initial documentation PR should target feature/knowledge-rag-v0, not develop, to avoid including unrelated unmerged history. CLAUDE.md is ignored by inherited rules and needs an exact-file force-add only after approval.

[Task 6.1B error analysis](TASK-6.1B-TEST-ERROR-ANALYSIS.md) establishes one oversized parameter-ID case with setup and teardown errors. No application or frozen-test change was made; the milestone remains incomplete.
