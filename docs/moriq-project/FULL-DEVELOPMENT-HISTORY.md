# Development history and evidence precedence
Dates below come from Git or dated recovered reports. Test counts in this history are historical unless explicitly identified in the migration test report. GitHub PR bodies contain stale intermediate statements and must be read alongside current heads and later local closeouts.

|Milestone|Verified implementation and checkpoint|Validation, problems and disposition|
|---|---|---|
|Task 1, October 6|Open WebUI 0.11.4 baseline 8bd8b4fac5e059578ac0c74b3c18d11139f88b7d; initial docs commit 714b0550af6c69f3c7c9bfc5a6cd302659602307 preserved by incremental bundle; setup branch now 66e6b1167a723a1dec5fc1a39a92d7a0171005b9|Bootstrap report records Windows build EPERM, dependency extraction failures and unverified full-stack runtime. No-test-files frontend exit 0 is not coverage.|
|Task 2, October 9|Brain 0.1 prompt/config/native workspace import, 50cb6533f62cd2f28bcf7a236c5f2868fe05bb1f; merged into develop at 1a9d5a973bd5205f74d512b2bc417f2c7e00abb9|Eight historical helper/schema checks. Later deployment PR11 records active/private qwen3:4b import and one successful smoke answer; broad behavior failed.|
|Deployment, October 9–12|PR11, feature/local-deployment, 567e4332e68e391579cb110c6504b70335e382ec|Localhost Compose 3000, persistent volume, Windows helper; 2/12 behavioral passes. CPU responses 57.859–307.698s, median 217.670s. Current runtime not reactivated.|
|3.0/3.1 screening|V0.2 and V0.2.1 experimental prompts and preserved evaluations|48 paired observations; no deployed candidate. Instruct small screen 1/6 overall for each prompt. Faster delivery did not establish correctness.|
|3.3 source enforcement|05a7d9de7; isolated source_gate|Missing evidence blocks generation; 15 new +15 existing checks. Valid IDs cannot certify prose.|
|3.4 adversarial review|9f487f08f; fixed public draft leak and validation defects|Frozen baseline 6 pass/6 fail methods; final 12/12 adversarial, 32 total gate methods. Failed evidence retained.|
|3.5–3.8|Private/public boundary, attestation lifecycle, 3.6 identity-binding defect and 3.6.1 correction; security review and frozen mock harness. 6aa0ee581897bd345e7e143063d030b6dc181d01|3.6.1/3.7 recorded 77 across all suites (not source gate alone); 3.8 recorded 95 =80 gate+4 V0.2+3 V0.2.1+8 Brain, including 16 frozen harness checks. Review source_gate reports for exact selections.|
|3.9/3.10, October 14|Fake HTTP transport and offline closeout 21a03cc2af98cf8a0a0d6541ffdc1fbf35e07bfb|108 historical offline tests, 16 frozen checks included. PR12 currently published at this SHA; earlier push-blocked wording is historical.|
|4.1|Initial isolated retrieval architecture (ce13fc182, 8f5f5b643, 6bc8e187a)|Scope and unit tests precede registry implementation; not live RAG.|
|4.2, October 14|Registry/ingestion bc63123c557668a9fec4ec726897ad98eae9f3e2|Independent synthetic reviewer, exact bytes, provenance and deterministic chunks.|
|4.3, October 16|Retrieval/citations 8cd7fba10b45223992963a28dba6551944f95b88|Bounded lexical ranking, exact scope filters, revocation and citation identity checks.|
|4.4A, October 17|Offline preflight cd96dbde6a4b31b3e26e4242ee1cdb8ccdb779e0|53 preflight methods; educational sources are refused by code-only scope.|
|4.4B, October 19|Lifecycle a1406ddf88a73f2e22c102439f8fe3fc83e6d4c3|95 lifecycle tests: 80 variants across 44 IDs plus 15 supplemental tests.|
|4.5F, October 20|Synthetic pilot 8922647d536e6610d16374df8a2cb2b1e2ac64b6|38 tests, 24 registry and 14 authority. Five real educational drafts and C01 remain unapproved.|
|4.6B, October 21|Frozen evaluation 830f065fc2e7af30484e22206e05f42bfb711828|54 cases/116 variants and two supplements; 85 registry+30 authority methods; three composite gates are not extra pytest methods.|
|4.7, October 23–27|Checkout byte policy b78466029a751825c75424ff14d80e2bc82ee631; I/J/K/O investigations and later owner acceptance|J E24 failure, missing exit and unexplained pauses retained. Later O: three checkout policies, H15 hashes and nine benchmarks. Owner-led offline amendment accepted; original independent V12 unmet.|
|5.1–5.2D, October 26 onward|Standalone Studio HTML/CSS/JS, authentic Courtyard Villa image, responsive/citation/keyboard refinement|No whole Open WebUI frontend replacement. Evidence includes 320/390/768/1280 widths.|
|5.3|Local chat persistence, rename, confirmed delete and recovery|Fixture storage tests; not server-side conversation persistence.|
|5.4/5.4B, October 30|Final visual review of single-image design|No second approved hero; carousel remains asset-blocked. 200% zoom blocked, screen reader and physical-device checks untested.|
|6.0, October 30|Readiness, risk, integration map and plan|Separate components, no full system connection.|
|6.1A, November 2|offline_integration/contracts.py, test_contracts.py, README.md; untracked on b784660|Historical 66 focused +525 existing tests, 122 subtests. Host capabilities, fixed public status, no generation/retrieval/private view.|
|6.1B, November 2|Untracked backend.py and test_backend.py also recovered|Saved first backend run: 56 passed, 2 errors in setup/teardown of an oversized parameterized test ID (Windows environment variable limit 32767). No completed closeout found. Preserve and assess; do not restart or call it complete.|

Historical reports are retained byte-for-byte in the Desktop task evidence folders and private content-addressed backup. The older TASK_4_FINAL_ACCEPTANCE_STATUS and unsigned amendment template remain historical; the dated TASK_4_FINAL_CLOSEOUT and owner adoption record explain the narrower acceptance. None establishes independent review or production authorization.
