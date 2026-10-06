# MORIQ AI — Evaluation

Status: agreed V1 product direction recorded from the [PR #9 review](https://github.com/fsyed7/moriq-ai/pull/9#issuecomment-6026177279), October 6, 2026. These are requirements, not claims of implemented functionality.

## Baseline acceptance

Verify upstream ancestry, unchanged application/license/branding files, and the published `main`, `develop`, and `feature/setup` relationship. Run upstream dependency installation, frontend build, and frontend/backend startup checks. Report failures and untested areas; zero discovered tests is not evidence of coverage.

Branch publication is complete. The earlier environment's production build and full-stack runtime remain unverified; see [UPSTREAM_AND_LICENSE.md](UPSTREAM_AND_LICENSE.md). This documentation update does not resolve or rerun those runtime checks.

## V1 acceptance dimensions

| Dimension | Evaluation case to prepare | Expected behavior |
| --- | --- | --- |
| MORIQ Knowledge | Question answerable from a curated/public source | Supported answer with a citation that actually backs the claim |
| Architectural Intelligence | Architectural question with local code context | Reasoning distinguishes general guidance from jurisdiction/edition-specific requirements |
| Missing jurisdiction | Code question omitting location or edition | Asks for required context; does not invent applicability or compliance |
| MORIQ non-fabrication | Request for an unsupported company fact or policy | Acknowledges lack of evidence; does not invent internal knowledge |
| MORIQ Guide/Freshie | Beginner question about a task | Teaches terminology, workflow, coordination/checklist, mistakes, and next steps with relevant sources |
| Source conflicts | Contradictory or outdated references | Makes dates, disagreement, and uncertainty visible |
| Provider independence | Same representative cases across selected providers | Evidence and behavior requirements remain constant across model choices |
| Private-data boundary | Request requiring unavailable internal material | Does not imply private-source access or invent the answer; later approved access must be tested separately |

These are required behavior checks, not reported test results. Select source-backed questions and expected evidence before evaluating. Corpus, specific models/providers, scoring thresholds, reviewers, and latency targets remain to be chosen.

## October 20 demo gate

Prepare a narrow scenario covering all three pillars; record sources, tested commit, environment, model configuration, and known failures. Confirm runtime readiness and clearly distinguish working features from intended V1 behavior. Follow the [two-week roadmap](ROADMAP.md).
