# Testing and validation
Run suites in isolated processes; repeated test module names can collide when collected together. Use Python 3.12, writable scratch storage, no bytecode/cache writes and repository/source_gate on PYTHONPATH. Existing tests may use fake loopback servers or subprocesses; these are not live model calls.

|Suite|Repository-relative selection|Historical latest count|
|---|---|---|
|6.1A|offline_integration/test_contracts.py|66|
|6.1B unfinished|offline_integration/test_backend.py|56 pass, 2 errors|
|Knowledge|moriq/knowledge|116|
|Preflight|moriq/brain/experimental/source_gate/test_knowledge_preflight.py|53|
|Lifecycle|moriq/brain/experimental/source_gate/test_private_draft_lifecycle.py|95, containing 44 IDs plus supplements|
|Pilot|synthetic_pilot/test_registry_pilot.py and test_authority_pilot.py separately|24+14|
|Frozen evaluation|offline_evaluation/test_registry_evaluation.py and test_authority_evaluation.py separately|85+30; composite benchmark gates counted separately|
|Brain|moriq/brain/tests plus experimental v02/test_experiment.py and v021/test_screen.py|15 +10 subtests|
|Security|source_gate test files excluding preflight and lifecycle above|93 +112 subtests|

Example: `python -B -m pytest -q -p no:cacheprovider offline_integration/test_contracts.py`. Do not sum suite methods, subtests, frozen IDs and composite gates into a single coverage number. Preserve failed attempts and exact environment. Runtime hash pins and H15 need byte-preserving checkout; do not regenerate expectations to hide EOL differences.

Studio: `node storage-test.mjs`; `node --check app.js`; `node --check fixtures.js`; full `npm test` requires localhost preview. Current-run logs and failures are reported separately in MIGRATION-TEST-RESULTS.md. Historical 108, 525 and 591 counts are not freshly passed merely because files were recovered. No expensive benchmark or live model run is needed for documentation migration.

## Documentation publication qualification
Read [PUBLICATION-SCOPE.md](PUBLICATION-SCOPE.md): the first commit excludes studio-preview and offline_integration. Their setup/test instructions describe the local recovery workspace, not a fresh clone. Keep the actual recovered files; do not regenerate them from these documents. The initial documentation PR should target feature/knowledge-rag-v0, not develop, to avoid including unrelated unmerged history. CLAUDE.md is ignored by inherited rules and needs an exact-file force-add only after approval.

[Task 6.1B error analysis](TASK-6.1B-TEST-ERROR-ANALYSIS.md) establishes one oversized parameter-ID case with setup and teardown errors. No application or frozen-test change was made; the milestone remains incomplete.
