# MORIQ AI
Architectural Intelligence & Knowledge Assistant, built on the preserved Open WebUI foundation.

MORIQ aims to combine source-aware architectural reasoning, project knowledge and a dark architectural Studio interface. **Current status: offline prototypes and local fixture UI; V1 integration is incomplete.** Historical live Brain behavior failed its release gate. No production readiness is claimed.

- Brain: versioned workspace-model prompt/configuration.
- Reliability: isolated source enforcement, private drafts and mock transport.
- Knowledge: approved synthetic registry, bounded retrieval, citation identity and lifecycle tests.
- Studio: responsive HTML/CSS/JS fixture preview with local chat state and authentic approved local hero.
- Integration: completed local 6.1A contracts plus unfinished, untracked 6.1B work.

The source retains Svelte/TypeScript src, FastAPI/Python backend and moriq modules. Studio remains separately launched under studio-preview. See [architecture](docs/moriq-project/SYSTEM-ARCHITECTURE.md), [current status](docs/moriq-project/CURRENT-PROJECT-STATUS.md) and [V1 roadmap](docs/moriq-project/ROADMAP-TO-V1.md).

## Development
Read [setup](docs/moriq-project/DEVELOPER-SETUP.md) before installing or launching anything. For the fixture UI, run npm run dev from studio-preview and open localhost:5175; npm test requires that local preview. Offline Python checks use Python 3.12 and the documented import paths. See [test commands](docs/moriq-project/TESTING-AND-VALIDATION.md) and [actual migration results](docs/moriq-project/MIGRATION-TEST-RESULTS.md). Full upstream setup/build/runtime has not been freshly validated.

## Documentation and review
[Complete documentation index](docs/moriq-project/DOCUMENTATION-INDEX.md) · [History](docs/moriq-project/FULL-DEVELOPMENT-HISTORY.md) · [Claude handoff](CLAUDE.md) · [Agent rules](AGENTS.md) · [Contributing](CONTRIBUTING.md) · [MORIQ changelog](MORIQ-CHANGELOG.md).

PR11, PR12 and PR13 remain draft/unmerged; PR13 depends on PR12. The migration branch and documentation are uncommitted. Private backup/media inventories and screenshots remain outside the proposed public publication scope until rights review. See [GitHub plan](docs/moriq-project/GITHUB-RECONCILIATION-PLAN.md).

## Safety and attribution
Citation validity is not claim truth; ingestion approval does not authorize answer release. Live inference, real-source ingestion, automatic release and deployment remain restricted. Read [security limitations](docs/moriq-project/SECURITY-AND-LIMITATIONS.md).

[LICENSE](LICENSE), [license history](LICENSE_HISTORY), [notice](LICENSE_NOTICE) and upstream history are preserved. [Original Open WebUI README](README-OPEN-WEBUI.md) is retained unchanged as historical upstream documentation; its broad runtime commands are not migration authorization. [License and asset review](docs/moriq-project/LICENSE-AND-ATTRIBUTION.md) remains necessary before redistribution.

## Publication boundary
This first proposed commit is documentation-only. Studio and offline_integration are recovered local work and are excluded from it; a fresh GitHub clone will not contain them. The launch and integration-test commands above apply to the local recovery copy. See [exact scope and branch base](docs/moriq-project/PUBLICATION-SCOPE.md). No source integration or deployment is implied.
