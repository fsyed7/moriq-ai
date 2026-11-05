# MORIQ AI — agent orientation
Goal: an AI assistant only for architects and engineers at MORIQ. Version 1 is a working single-user prototype in moriq/app; see README.md and moriq/app/README.md.

Read [current status](docs/moriq-project/CURRENT-PROJECT-STATUS.md), [security limits](docs/moriq-project/SECURITY-AND-LIMITATIONS.md) and the [Task 6.1B closeout](docs/moriq-project/TASK-6.1B-CLOSEOUT.md) before larger changes.

Source: moriq/app is the app; moriq/brain is the prompt; moriq/knowledge is registry and retrieval; experimental/source_gate holds review boundaries; offline_evaluation, offline_integration and synthetic_pilot hold frozen offline tests; studio-preview holds the design. backend and src are inherited Open WebUI; moriq/brain/tests reads backend paths, so do not move them.

Tests: py -3.12 -B -m unittest moriq.app.test_app moriq.app.test_security, and py -3.12 -B -m moriq.app.evaluate for a live check. Run other suites in isolated processes as described in the testing document; they need an existing pytest 9.0.0.

Ten tracked files show as modified locally (three EOL-only differences, seven byte-identical to HEAD). Do not stage them or normalize their line endings. main is the working branch; earlier branches are archive/* tags.

On 2026-11-04 the owner told agents to build without per-step permission, and accepted having no reviewer for now. That does not cover publishing the Courtyard Villa image, real or unlicensed sources, or presenting answers as verified. Source approval is not answer release; citation identity is not claim truth. Original V12 independent review remains unmet. Never claim a review or acceptance that did not happen.
