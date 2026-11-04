# Contributing to MORIQ
Read CLAUDE.md, the current status, architecture, security limits and relevant historical evidence first. Preserve existing Python/JS conventions and locked dependencies. Keep changes bounded to the approved task; avoid source relocations during documentation work. Version prompt/config changes together and preserve approved media and frozen fixtures.

Existing main/develop and feature branches remain unchanged. Use docs/*, feature/* or fix/* according to scope. Do not invent a new integration branch policy or automatically merge stacked draft PRs. This owner requires explicit approval before commits, pushes, merges, remote branch deletion/replacement or publication. Local preparation is not that approval.

Before review: document the trigger and resulting behavior, exact scope, acceptance criteria, tests actually run, known failures and limitations. Include security review when boundaries change; verify no unintended source/evidence edits. Update status, relevant ADR and MORIQ changelog. Use a focused conventional commit message after approval. Tests and docs cannot substitute for accountable release acceptance.
