# MORIQ AI — Upstream, license, and bootstrap record

Recorded: October 6, 2026. Task: [issue #1](https://github.com/fsyed7/moriq-ai/issues/1).

## Exact source

- Official source: <https://github.com/open-webui/open-webui.git>
- Selected branch: official `main` (released baseline; package version `0.11.4`).
- Exact commit: **`8bd8b4fac5e059578ac0c74b3c18d11139f88b7d`**.
- [Immutable upstream commit](https://github.com/open-webui/open-webui/commit/8bd8b4fac5e059578ac0c74b3c18d11139f88b7d).
- Target remains **`fsyed7/moriq-ai`**. The target was empty before the initial import; the three branches are now published.
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

**Publication is complete.** Remote refs verified on October 6, 2026 before the PR #9 documentation correction:

| Published branch | Verified head before this correction |
| --- | --- |
| [main](https://github.com/fsyed7/moriq-ai/tree/main) | `8bd8b4fac5e059578ac0c74b3c18d11139f88b7d` |
| [develop](https://github.com/fsyed7/moriq-ai/tree/develop) | `8bd8b4fac5e059578ac0c74b3c18d11139f88b7d` |
| [feature/setup](https://github.com/fsyed7/moriq-ai/tree/feature/setup) | `714b0550af6c69f3c7c9bfc5a6cd302659602307` |

`main` equals the pinned upstream baseline and `develop` equals `main`. Documentation corrections are subsequent commits on `feature/setup`; the table records the initial published heads, not a permanent feature-branch SHA. [PR #9](https://github.com/fsyed7/moriq-ai/pull/9) targets `develop` and remains unmerged.

Remotes are clone-local configuration, not tracked files. For a new checkout of the published repository:

```sh
git clone https://github.com/fsyed7/moriq-ai.git moriq-ai
cd moriq-ai
git remote add upstream https://github.com/open-webui/open-webui.git
git config remote.pushDefault origin
git switch --track origin/feature/setup
```

For an existing checkout, inspect refs and local work first and add `upstream` only if absent. Never force-push the baseline. Fetch and review future upstream updates on a separate branch, record the new SHA, and rerun validation before an approved merge.

## Publishing safeguards

The PR #9 description records that repository Actions remain disabled during the initial import while inherited publishing workflows are reviewed. This documentation correction does not change Actions settings or workflow files, and does not independently certify the current setting through the administration API.

Unmodified upstream `docker.yaml` publishes images (including a hardcoded Docker Hub destination), `release.yml` creates releases and dispatches Docker builds, and `release-pypi.yml` attempts package publication. Keep these publishing paths disabled until downstream release behavior is reviewed. Retain useful frontend/backend/regression CI rather than deleting workflow history; verify publishing workflows are disabled before re-enabling repository Actions. The exact upstream baseline remains unchanged.

Future documentation updates should push only `feature/setup`, with normal fast-forward protection. Inspect remote state before pushing; if it differs unexpectedly, review rather than overwrite. Do not merge PR #9 as part of this correction.

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
| Branch publication | COMPLETE: `main`, `develop`, and `feature/setup` published; verified heads recorded above. The earlier sandbox credential failure is historical, not a pending publication task |

The Pyodide preparation step modifies tracked `static/pyodide/pyodide-lock.json` while fetching assets. That generated change was excluded/restored to the pinned baseline before the documentation commit. No application-source repair or dependency change was made to work around environment failures.

**Branch publication is complete; issue #1 still requires successful production-build and full local runtime validation.** These results describe this environment; they neither prove the baseline broken on a supported host nor claim successful runtime validation.
