# Backup strategy
Before a future engineering checkpoint, record branch/HEAD/status, refs, stashes, worktrees and ignored source; snapshot unique working bytes and Git metadata. Preserve untracked code and evidence alongside a SHA-256 manifest. Verify recovery to a new empty location before declaring success. Git alone does not preserve uncommitted or ignored work.

Keep private content, credentials and live database snapshots outside public repositories and cloud publishing packages. A logical application-data backup must use a service-appropriate consistent snapshot procedure; do not copy a live SQLite database blindly. Docker named volumes and model caches are separate from source recovery.

The migration backup is local on the same disk. It protects against organization mistakes, not disk loss. A separately approved offline/external backup is recommended; no scheduled job or cloud sync was configured. See the local BACKUP-MANIFEST and RECOVERY-INSTRUCTIONS for this snapshot's exact coverage and exclusions.
