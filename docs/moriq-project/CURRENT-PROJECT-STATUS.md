# Current project status — verified 2026-11-04
Canonical working repository: Desktop/MORIQ AI/07 - Application Source/moriq-ai. Prepared local branch docs/migration-2026-11-04; HEAD b78466029a751825c75424ff14d80e2bc82ee631. No new commit or remote mutation. Original baseline branch remains feature/knowledge-rag-v0 in its original workspace.

Ten original tracked modifications were verified as LF/CRLF-only differences against HEAD and preserved exactly. All five offline_integration files remain untracked: contracts.py, test_contracts.py, README.md, backend.py and test_backend.py. 6.1A is the last completed integration checkpoint; newer 6.1B is incomplete. Studio was copied byte-for-byte into studio-preview without wiring it into upstream source.

Fresh validation is listed in MIGRATION-TEST-RESULTS.md, including errors/skips. Git integrity passed before migration; original Git objects and working bytes were backed up. Seven specified historical commit objects are present. main/develop/setup/Brain/UI and PR11–13 heads were independently checked through GitHub. Remote UI branch equals develop and does not contain the local Studio implementation.

Task 4 has dated owner-led offline acceptance under an amended criterion; original independent V12 remains unmet. Old pending status files are preserved as historical evidence, not silently rewritten. Production identity/audit/lifecycle, real-source rights/review, provider contract, cancellation/idleness, accessibility and deployment gates remain open.

This is one canonical development workspace containing distinct components, not a verified runnable integrated V1. Studio is independently runnable; offline Python suites exercise the backend. Full Open WebUI startup was not performed. Next: review and propose bounded completion of recovered Task 6.1B, preserving current code and freezing criteria before authorization.

## Documentation publication qualification
Read [PUBLICATION-SCOPE.md](PUBLICATION-SCOPE.md): the first commit excludes studio-preview and offline_integration. Their setup/test instructions describe the local recovery workspace, not a fresh clone. Keep the actual recovered files; do not regenerate them from these documents. The initial documentation PR should target feature/knowledge-rag-v0, not develop, to avoid including unrelated unmerged history. CLAUDE.md is ignored by inherited rules and needs an exact-file force-add only after approval.

[Task 6.1B error analysis](TASK-6.1B-TEST-ERROR-ANALYSIS.md) establishes one oversized parameter-ID case with setup and teardown errors. No application or frozen-test change was made; the milestone remains incomplete.
