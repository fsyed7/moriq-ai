# Migration test results — 2026-11-04

These runs executed against the restored canonical copy, using Python 3.12.14 with the pre-existing pytest installation exposed on sys.path. No dependencies were installed. Complete commands, cwd, elapsed time, XML and logs are in the local migration-tests directory referenced by the output review package. No model inference, real-source ingestion or production service start occurred.

|Selection|Exit|JUnit tests|Failures|Errors|Skipped|Seconds|
|---|---|---|---|---|---|---|
|contracts|0|66|0|0|0|6.95|
|backend|1|58|0|2|0|4.08|
|knowledge|0|116|0|0|0|3.41|
|preflight|0|53|0|0|0|5.30|
|lifecycle|0|95|0|0|0|9.55|
|pilot-registry|0|24|0|0|0|3.34|
|pilot-authority|0|14|0|0|0|3.22|
|registry|0|85|0|0|0|22.06|
|authority|0|30|0|0|0|9.62|
|security|1|205|2|0|0|40.64|
|brain|None|—|—|—|—|180.03|
|studio-storage|0|—|—|—|—|0.14|
|studio-syntax-app.js|0|—|—|—|—|0.12|
|studio-syntax-fixtures.js|0|—|—|—|—|0.14|
|studio-syntax-review.js|0|—|—|—|—|0.12|
|studio-syntax-server.mjs|0|—|—|—|—|0.12|
|security-network-granted|0|205|0|0|0|40.69|
|brain-network-granted|0|25|0|0|0|5.58|
|studio-http|0|—|—|—|—|6.30|

JUnit may represent subtests differently from pytest method summaries; do not add columns or historical acceptance IDs as independent coverage. The backend suite reproduced 56 passes and two setup/teardown errors because an oversized parameter ID exceeds Windows’ 32767-character environment-variable limit. Source was not fixed to make migration green. The first security run had two fake-HTTP failures; network-granted rows are separately recorded reruns with unchanged source and expectations. A timeout is not a pass. No failure is erased by a later run. Full upstream build/server tests, performance benchmarks, live model quality and new manual accessibility checks were not run.
