# MORIQ AI — agent orientation
Goal: finish V1 by connecting Studio, Brain, approved knowledge and backend lifecycle without weakening review boundaries. This is an offline prototype, not production.

Read [the index](docs/moriq-project/DOCUMENTATION-INDEX.md), [current status](docs/moriq-project/CURRENT-PROJECT-STATUS.md), [security limits](docs/moriq-project/SECURITY-AND-LIMITATIONS.md), [handoff](docs/moriq-project/CLAUDE-HANDOFF.md) and [test evidence](docs/moriq-project/MIGRATION-TEST-RESULTS.md) before editing.

Source: src and backend/open_webui are inherited; moriq/brain is prompt/config; experimental/source_gate holds review boundaries; moriq/knowledge is registry/retrieval. offline_evaluation and synthetic_pilot contain frozen offline tests. offline_integration includes untracked 6.1A and 6.1B; the owner accepted 6.1B as an offline facade only. studio-preview is the separate local fixture UI.

Migration branch docs/migration-2026-11-04 starts at b78466029a751825c75424ff14d80e2bc82ee631. Ten tracked files that show as modified (three EOL-only differences, seven byte-identical to HEAD) and five untracked integration files must be preserved. PR13 stacks on PR12; PR11 is separate; all remain draft/unmerged. Studio is not present on the remote UI branch.

Use Python 3.12 with the repository and source_gate on PYTHONPATH; isolated command: python -B -m pytest -q -p no:cacheprovider offline_integration/test_contracts.py. Full environment and outcomes are in the testing documents. Studio: npm run dev then npm test from studio-preview; port 5175. Do not activate models.

The owner accepted the [Task 6.1B closeout record](docs/moriq-project/TASK-6.1B-CLOSEOUT.md) on 2026-11-04. The first connected app is in moriq/app; see its README for how to run it and its limits. On 2026-11-04 the owner told agents to build without per-step permission, which does not cover publishing, real or unapproved sources, or releasing answers as verified. Never overwrite them as if the task had not started. Source approval is not answer release; citation identity is not claim truth. Original V12 independent review remains unmet.

No commit, push, merge, remote mutation, deployment, live inference, real/confidential ingestion, automatic answer release, disabled-adapter activation, fixture weakening, dependency upgrade or brand-image alteration without explicit authorization. See AGENTS.md for matching rules.

## Local versus published files
Read [publication scope](docs/moriq-project/PUBLICATION-SCOPE.md). Studio and offline_integration are local-only and excluded from the first documentation commit. Do not assume they exist in a fresh clone or recreate them from narrative; recover the verified originals or obtain the separately reviewed source checkpoint. CLAUDE.md matches the inherited .gitignore but has been tracked since the documentation commit; commit changes to it only with approval. The Windows error investigation is in [the test-error report](docs/moriq-project/TASK-6.1B-TEST-ERROR-ANALYSIS.md).
