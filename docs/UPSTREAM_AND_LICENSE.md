# MORIQ AI — Upstream, license, and bootstrap record

Recorded: October 6, 2026. Task: [issue #1](https://github.com/fsyed7/moriq-ai/issues/1).

## Exact source

- Official source: <https://github.com/open-webui/open-webui.git>
- Selected branch: official `main` (released baseline; package version `0.11.4`).
- Exact commit: **`8bd8b4fac5e059578ac0c74b3c18d11139f88b7d`**.
- [Immutable upstream commit](https://github.com/open-webui/open-webui/commit/8bd8b4fac5e059578ac0c74b3c18d11139f88b7d).
- Target remains **`fsyed7/moriq-ai`**. The target had no refs when inspected.
- Full ancestry: 18,717 reachable commits; not a shallow clone. A blob-filtered clone retains original commits and fetches historical file contents on demand. No squash or replacement root commit was created.

The official development guide recommends upstream `dev` for contributing to its next release. This bootstrap intentionally selects released `main` and applies the source-development commands to that pinned baseline. MORIQ `develop` is our branch, not upstream `dev`.

## Remotes and branch workflow

```text
origin   https://github.com/fsyed7/moriq-ai.git
upstream https://github.com/open-webui/open-webui.git

main          8bd8b4fac5e059578ac0c74b3c18d11139f88b7d
develop       8bd8b4fac5e059578ac0c74b3c18d11139f88b7d
feature/setup documentation commit(s) directly above develop
```

These branches and remotes are configured locally. `remote.pushDefault` is `origin`. **Remote publication is pending:** Windows sandbox access to Git Credential Manager was denied; no push completed. Do not read this document as proof that the branches exist on GitHub. `feature/setup` remains unmerged.

Remotes are clone-local configuration, not tracked files. Reproduce from an empty local destination:

```sh
git init moriq-ai
cd moriq-ai
git remote add upstream https://github.com/open-webui/open-webui.git
git remote add origin https://github.com/fsyed7/moriq-ai.git
git config remote.pushDefault origin
git fetch --no-tags upstream main
git switch -c main 8bd8b4fac5e059578ac0c74b3c18d11139f88b7d
git switch -c develop
git switch -c feature/setup
```

For an existing target clone, add `upstream` if absent. Inspect existing refs and work before any branch change; never force-push the baseline. Future upstream updates should be fetched, reviewed for license/security changes, and integrated on a separate review branch. Record each new upstream SHA and rerun validation before an approved merge.

## Publishing precaution

Unmodified upstream `.github/workflows/docker.yaml` publishes container images on `main` pushes, and `release.yml` can create releases. Before the initial push, disable the inherited publishing workflows or temporarily disable repository Actions in GitHub settings, with the owner aware of that setting change. Keep the Git baseline untouched. Do not re-enable publishing until the downstream release process has been reviewed. No Actions settings were changed in this task.

Once authentication works and publishing is controlled, recheck that the remote is still empty (or contains only matching refs), then use a normal, non-forced push:

```sh
git ls-remote origin
git push --atomic origin main develop feature/setup
git branch --set-upstream-to=origin/main main
git branch --set-upstream-to=origin/develop develop
git branch --set-upstream-to=origin/feature/setup feature/setup
git ls-remote origin refs/heads/main refs/heads/develop refs/heads/feature/setup
```

If remote history differs, stop and review it rather than overwriting it. Do not merge `feature/setup`.

## License and branding review

The pinned [LICENSE](../LICENSE), [LICENSE_NOTICE](../LICENSE_NOTICE), [LICENSE_HISTORY](../LICENSE_HISTORY), and [CONTRIBUTOR_LICENSE_AGREEMENT](../CONTRIBUTOR_LICENSE_AGREEMENT) are retained unchanged and govern this baseline. This is a multi-license codebase, not uniformly MIT.

- Source redistribution retains copyright, conditions, and disclaimer; binary distribution reproduces them in accompanying materials. No endorsement by upstream or its contributors may be implied without permission.
- The current license restricts alteration, removal, replacement, or obscuring of Open WebUI branding. Exceptions cover at most 50 individual direct-access users in any rolling 30-day period, specific prior written permission, or an executed enterprise license expressly allowing modification. This bootstrap invokes no exception and changes no branding.
- `LICENSE_NOTICE` identifies MIT code before `a76068d69cd59568b920dfab85dc573dbbb8f131`, BSD-3-Clause code from there through `60d84a3aae9802339705826e9095e272e3c83623`, and subsequent contributed/modified code under the Open WebUI License. Historical terms remain applicable.
- The upstream CLA grants Open WebUI Inc. broad copyright/patent rights for contributions and requires sufficient contributor rights. Review it before submitting upstream contributions; this task does not invent a MORIQ contributor policy.

See the [pinned license](https://github.com/open-webui/open-webui/blob/8bd8b4fac5e059578ac0c74b3c18d11139f88b7d/LICENSE) and [official explanation](https://docs.openwebui.com/license/). A future branding decision needs a fresh review of the governing text and actual deployment facts.

The [official brand guidelines](https://docs.openwebui.com/brand/) call for the name “Open WebUI,” unmodified supplied assets, clear space and visibility, and no implied endorsement or incorporation into another company's brand. Naming this GitHub repository `moriq-ai` does not change the application or its package names. All existing branding, attribution, notices, and license files remain intact.

Third-party dependencies and bundled assets retain their own terms; this bootstrap is not a complete dependency license audit.

## Supported source-development workflow

Reference: [official development guide](https://docs.openwebui.com/getting-started/advanced-topics/development/), inspected October 6, 2026. The pinned `package.json` restricts Node to at most 22.x; use Node 22 and Python 3.11 or 3.12. The guide uses separate frontend/backend terminals.

Frontend from repository root:

```sh
cp .env.example .env
npm ci --no-audit --no-fund
npm run build
npm run test:frontend -- --run
npm run dev
```

Upstream documents `npm install`; `npm ci` uses the committed lockfile and matches its unit-test workflow. Upstream documents `--force` if dependency compatibility requires it; the installation here did not need it. The local run skipped downloading the Cypress binary (`CYPRESS_INSTALL_BINARY=0`); no Cypress/end-to-end testing is claimed.

Backend in a separate terminal:

```sh
cd backend
python -m venv venv
source venv/bin/activate
# Windows PowerShell activation: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt -U
sh dev.sh
```

On Windows without a POSIX shell, invoke the same Uvicorn entry point with a loopback bind in PowerShell:

```powershell
$env:CORS_ALLOW_ORIGIN='http://localhost:5173;http://localhost:8080'
python -m uvicorn open_webui.main:app --port 8080 --host 127.0.0.1 --reload
```

Use isolated development data and a local `.env`/environment for secrets; neither belongs in Git. Confirm backend `/health`, frontend `http://localhost:5173`, and browser-to-backend requests before considering local runtime acceptance complete. A model response additionally requires an authorized provider/model configuration, which was not supplied here.

## Validation record

Environment: Windows; isolated Node **22.20.0**, npm **10.9.3**, Python **3.12.14**, Ruff **0.16.10**. Dependencies and logs stay outside committed documentation; no lockfile upgrades are included.

| Check | Actual result |
| --- | --- |
| Upstream SHA and ancestry | Verified exact SHA above, 18,717 commits, non-shallow history |
| Frontend dependency install | `npm ci --no-audit --no-fund`: PASS, 1,119 packages; upstream deprecation warnings |
| Frontend production build | FAILED twice: Vite `EPERM` on `realpath` for `node_modules/@sveltejs/kit/src/runtime/server/index.js` |
| Frontend unit command | `npm run test:frontend -- --run`: exit 0, **no test files found**; no unit coverage demonstrated |
| Frontend type check | `npm run check`: stopped after several minutes without a final result; NOT VERIFIED |
| Frontend development smoke | Vite announced ready on `127.0.0.1:5173` with dependency-resolution warnings; HTTP request timed out after 20 seconds; server stopped |
| Backend dependency install | BLOCKED: pip extraction of `langdetect` hit Windows access denied; uv retry hit access denied canonicalizing an `antlr4-python3-runtime` extraction directory |
| Python formatting | `ruff format --check . --exclude .venv --exclude venv`: PASS, 285 files already formatted |
| Python logic checks | `ruff check --select=F --ignore=F401,F403,F405,F541,F811,F841 .`: PASS |
| Backend runtime / full-stack smoke | NOT VERIFIED: backend dependencies could not be installed; Docker engine unavailable and WSL access denied |
| Git push | BLOCKED: Git Credential Manager credential enumeration denied by Windows sandbox; dry-run failed before any push |

The Pyodide preparation step modifies tracked `static/pyodide/pyodide-lock.json` while fetching assets. That generated change was excluded/restored to the pinned baseline before the documentation commit. No application-source repair or dependency change was made to work around environment failures.

**Issue #1 remains incomplete until the production build, full local run, and remote branch publication succeed.** These results describe this environment; they neither prove the baseline broken on a supported host nor claim successful runtime validation.
