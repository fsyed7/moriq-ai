# MORIQ AI — Evaluation

Status: Day 1 baseline checks plus a proposed V1 evaluation outline.

## Baseline acceptance

Verify exact upstream ancestry, unchanged application/license/branding files, configured remotes, and the `main` → `develop` → `feature/setup` branch relationship. Run upstream dependency installation, frontend build and test commands, and development server smoke checks where supported by the environment. Record failures and untested areas explicitly; a command that discovers zero tests is not application test coverage.

Actual commands and outcomes are recorded in [UPSTREAM_AND_LICENSE.md](UPSTREAM_AND_LICENSE.md). Bootstrap issue #1 must not be considered fully validated until full local frontend/backend startup has been demonstrated.

## Proposed V1 evaluation dimensions

After requirements and sources are approved, define representative questions, source-grounded expected answers, citation correctness, unsupported-question handling, access isolation, and relevant latency measures. Dataset, thresholds, reviewers, and model/provider remain TBD. No scores or successful MORIQ behavior are claimed.

## Demo gate

Before October 20, 2026: agree a demo script, use approved data, record the tested commit and environment, review known failures, and identify which parts are implemented versus proposed.
