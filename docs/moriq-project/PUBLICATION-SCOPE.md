# First documentation publication scope
Status: prepared locally for explicit owner approval. No commit, push or PR creation has occurred.

Destination branch: docs/migration-2026-11-04, based on b78466029a751825c75424ff14d80e2bc82ee631. Proposed PR base: feature/knowledge-rag-v0 at that checkpoint. Opening this PR against develop would also include the unmerged Task 3/4 history; that is not a documentation-only review. PR13 remains stacked on PR12 and is not merged by this proposal.

The first proposed commit contains only the named root documentation files and docs/moriq-project Markdown files listed individually in the external review manifest. README-OPEN-WEBUI.md preserves the previous root README byte-for-byte. LICENSE, LICENSE_HISTORY, LICENSE_NOTICE, contributor agreement, upstream CHANGELOG, application code, tests, dependency locks and ignore rules remain unchanged.

## Local recovery versus a GitHub clone
The Desktop recovery copy contains studio-preview and five offline_integration files. These are untracked local artifacts and are EXCLUDED from this first commit. The ten historical working-byte restorations are also excluded. A fresh clone of the proposed documentation branch will therefore NOT contain Studio or the 6.1A/6.1B implementation. Local commands for those components apply only after separately authorized recovery or source publication. GitHub documentation publication is not source integration or a deployable release.

Private backup objects, provenance CSVs with machine paths, archived task evidence, photos/videos, live data and local diagnostic logs remain outside the proposed commit. Their source records are available in the owner's local migration review package, not promised as downloadable GitHub assets. Current-state documents describe the dated local checkpoint; verify actual files after cloning.

The inherited .gitignore excludes CLAUDE.md. After explicit approval only, the operator must add that exact reviewed file with git add -f -- CLAUDE.md. Do not use git add -A, force-add directories, or alter ignore rules to sweep in local artifacts. Every other path must be added explicitly from the approved manifest. Nothing is staged now.

The first public README will appear only on the new branch. It will not change the default branch or merge existing PRs. Licenses and attribution remain applicable; no media distribution rights or branding exception are inferred. See [GitHub reconciliation](GITHUB-RECONCILIATION-PLAN.md) and [license review](LICENSE-AND-ATTRIBUTION.md).
