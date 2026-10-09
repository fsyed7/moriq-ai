# Task 3 validation record — October 9, 2026

**Deployment incomplete; Brain not activated.** No running model or behavior
quality is claimed. Base: `develop` at
`1a9d5a973bd5205f74d512b2bc417f2c7e00abb9` (PR #10), verified through GitHub.
Branch: `feature/local-deployment`.

## Docker evidence and diagnosis

- CLI: Docker 27.4.0, API 1.47, context `desktop-linux`. Compose 2.31.0.
- `docker version`, container/image/volume inventory calls all fail with
  `open //./pipe/dockerDesktopLinuxEngine: Access is denied` in this execution
  environment. Server version, current container state, retained layers, volume
  contents and name conflicts could not be verified. No bypass was attempted.
- Docker Desktop host log records a `v0.11.4` image pull at **16:41:13 EDT**.
  At **16:44:03 EDT**, WSL bootstrap exits with status 1, the engine stops
  unexpectedly, event streams report `unexpected EOF`, and the proxy reports
  `no connected VM`. A WSL disk-detach operation also reports `0x80072746`.
  The logs subsequently show a WSL reboot and successful API proxy requests.
  A second image pull at 16:46:15 is canceled at 16:48:14. These are historical
  observations, not proof that the engine is currently healthy.
- The EOF is consistent with the observed engine interruption during the pull.
  **The underlying reason for WSL termination is not established.** Disk
  exhaustion is a strong concern, not a proven causal explanation of that event.
- The attempted fresh repository clone independently failed with
  `No space left on device`. Drive C: then had **67,411,968 bytes (about 64 MiB)**
  free. Further large downloads were stopped. Nothing was deleted to free space.
  A later check showed 4,431,028,224 bytes (about 4.13 GiB) free; the cause of
  that change was not established. It remains below the helper's 10 GiB policy.
- Port 3000 showed no TCP listener at inspection time. Requests to
  `http://127.0.0.1:3000/health` and `http://127.0.0.1:11434/api/tags` were refused.
  This does not establish the contents of any existing application database.

Raw local Docker logs were inspected in place; they are not committed. No Docker
settings, engine permissions, containers, images, volumes or accounts were changed.

## Prepared changes

- Standalone Compose config pinned to the repository's Open WebUI version,
  localhost binding, existing named persistent storage, readiness health check,
  bounded logs and persistent upstream-generated secret-key location.
- PowerShell lifecycle helper with fail-fast engine, disk, port, name and
  pre-existing-volume checks; no automatic deletion or container recreation.
- Ignored local configuration, backups and generated Brain artifacts.
- Startup/recovery, secret preservation, provider selection, admin login,
  activation and evaluation instructions in `LOCAL_DEPLOYMENT.md`.
- Mocked launcher guard tests. Upstream application code and licenses unchanged.

## Checks actually executed

| Check | Result |
| --- | --- |
| Existing Brain unittest suite | **8 passed**, no skips; Python 3.12.14 / Pydantic 2.13.5 |
| `ruff check moriq/brain` | **Passed**, Ruff 0.16.10 |
| `ruff format --check moriq/brain` | **Passed**, 4 files formatted |
| `docker compose -f compose.local.yaml config --quiet` | **Passed**, no daemon needed |
| Rendered Compose inspection | **Passed**: 127.0.0.1 only, v0.11.4, named external volume, authentication enabled |
| PowerShell parser | **Passed**, no syntax errors |
| Launcher mocked guard checks | **6 passed**: denied engine, name conflict, disk full, port conflict, unreviewed volume, new-volume path |
| Launcher against real Docker | **Blocked as expected** at engine access; no mutation attempted |
| Git ignore checks | **Passed** for environment, backup and generated import paths |
| Staged Git diff/whitespace check | **Passed**, seven new files only |
| Runtime image digest / compatibility / health | **Not verified**, engine inaccessible and disk full |
| Provider configuration and response | **Not verified**, no available authenticated instance/model |
| Brain generation with real connected ID / import / selectable model | **Not run**, no verified model ID or admin session |
| Full upstream backend/frontend/build suites | **Not run**; full pinned dependencies not installed, no upstream code changed |

Pydantic differs from upstream's pinned 2.13.4; focused schema tests do not prove
full-server compatibility. Tests used a writable workspace TEMP/TMP directory.
Mocked launcher checks exercise control flow only; they do not prove Docker startup.

Reproduce focused checks from the repository root with Python 3.11/3.12,
Pydantic 2 and Ruff installed:

```powershell
python -m unittest discover -s moriq/brain/tests -v
python -m ruff check moriq/brain
python -m ruff format --check moriq/brain
docker compose -f compose.local.yaml config --quiet
./moriq/local/tests/test_manage.ps1
git diff --check
```

## Behavioral evaluations

All cases are **NOT RUN**, with zero live responses: `general`, `freshie`,
`freshie-transfer`, `moriq-no-source`, `code-no-jurisdiction`, `code-with-context`,
`recommendation`, `conflicting`, `missing`, `injection`, `code-source`, `concise`.
Architectural reasoning, knowledge reliability, Freshie teaching, provider
consistency, actual import, sharing and retrieval/citation rendering remain open.

## Remaining steps

1. Free or relocate data with explicit approval of the affected paths. Check
   Windows and Docker disk capacity. No cleanup/reset/prune is authorized here.
2. Use an authorized local execution environment with Docker engine access.
   Run `./moriq/local/manage.ps1 Check`; resolve any storage/name/port conflicts
   without data loss, then `Start` according to the existing-data procedure.
3. Verify healthy container, root-page response and image/version; record digest.
4. The owner completes admin signup/login. Configure or verify an authorized
   provider, test inference, and obtain the actual connected model ID.
5. Generate/import Brain through the supported UI after any existing-model backup.
   Verify selection and sharing; run/review all 12 cases three times each.

GitHub CLI authentication was invalid; publication uses the authenticated GitHub
connector instead. A sparse checkout sharing already-existing Git objects avoided
another large clone. Do not delete its source object store while using that local
checkout. The PR is a preparation deliverable, not a declaration of deployed readiness.
