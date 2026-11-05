# Known issues and blocker register
|Severity|Issue/evidence|Affected component|Next action|
|---|---|---|---|
|Critical / release gate|Production identity, audit, lifecycle and recovery are absent; original Task 4 risk register remains authoritative|Backend/security|Separate threat model and implementation authorization; retain all 16 original risks at their original severities|
|Critical / release gate|Real-source rights and qualified review unresolved; original V12 unmet|Knowledge/release|Accountable independent acceptance; do not infer from owner-led offline amendment|
|Closed|6.1B accepted by the owner on 2026-11-04 as an offline facade only. The earlier 2 setup/teardown errors from an oversized pytest ID were resolved by a label-only ID; the failed runs are retained|offline_integration/backend.py, test_backend.py|None for 6.1B; see [the closeout record](TASK-6.1B-CLOSEOUT.md)|
|Medium|6.1B coverage gaps: the oversized case cannot prove the size limit works; nesting depth, non-bytes payloads, lone surrogates and over-limit sources have no backend-level case|offline_integration/test_backend.py|Findings only in 6.1B; assess in Phase B|
|High|Five integration files are untracked and ten tracked files show as modified (three LF-to-CRLF differences, seven byte-identical to HEAD)|Git/recovery|Keep verified backup; review source publication separately from documentation|
|High|Studio is local-only and disconnected; UI branch remains at develop's Brain merge|Studio/integration|Preserve source, then plan an isolated connection with no private-text exposure|
|High|Historical live model factuality/behavior gates failed|Brain|No deployment promotion; separately authorize evaluation only after safety prerequisites|
|High|Full upstream build and runtime not freshly reproduced|Application|Resolve environment and run approved setup/build workflow without touching live data|
|Medium|200% zoom blocked; spoken screen reader/physical devices untested|Accessibility|Explicit manual/device verification and recorded disposition|
|Medium|Historical D/J latency failures unresolved|Evaluation|Retain I/J/K/O comparisons; no speculative root-cause claim|
|Medium|Official logo master and additional approved photographs absent|Brand|Obtain authentic assets and public redistribution permission|
|Review gate|Third-party/brand redistribution obligations not fully cleared|Publication|Review pinned license, notices, dependencies and media rights before release|

This table adds migration-level actions; it does not close or downgrade the 16 historical Task 4 risks. See the recovered task-4.7-risk-register.csv and dated owner closeout.
