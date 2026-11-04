# Task 6.1B Windows test-error investigation
Investigation date: 2026-11-04. Implementation and frozen test files were not changed. Task 6.1B remains incomplete.

## Reproduction and observed mechanism
Using Python 3.12.14 and pytest 9.0.0 with unrelated plugin autoload disabled, collect-only succeeded with 57 items. Normal execution reproduced 56 passes and two errors. These are setup and teardown errors for ONE collected case, not two independent failing assertions. The oversized case never reaches its test body in this run.

test_backend.py lines 101–103 parameterize payload with b'x' * 32769 and no explicit short IDs. Pytest derives an ID from the full bytes value. Observed node ID length: 32826 characters; adding the setup/teardown phase makes it longer still. Installed _pytest/runner.py calls _update_current_test_var before fixture setup and before teardown; it writes the node ID and phase to os.environ['PYTEST_CURRENT_TEST']. Windows rejects this environment update with ValueError: the environment variable is longer than 32767 characters.

An independent environment-variable probe, importing no application code, accepted a 100-character value and rejected tested values of 32766, 32767, 32768 and 32850 characters with the same ValueError. These are observed sample lengths, not a claim that the maximum value alone is exactly 32767; environment entry overhead matters. A shorter filesystem path cannot remove the 32769-character parameter content.

|Possible cause|Finding|
|---|---|
|Collection/discovery|Not the failure stage: all 57 cases collect successfully.|
|Windows path/node-ID handling|Root mechanism: oversized generated node ID exported as an environment variable; not a missing file or long filesystem-path failure.|
|Launcher configuration|The current launcher does not bound generated IDs. Disabling unrelated plugins does not prevent core pytest's environment update. No IDs or fixtures were changed during this investigation.|
|Permissions|No permission-denied exception. An independent local environment assignment reproduces the size error without network access or application imports. Elevation/network permission is not a remedy for this limit.|
|Test defect|A test portability defect in parameter labeling is established. The oversized payload itself is intentional boundary input and must remain unchanged.|
|Application defect|Not established by these two errors: the affected test body was not executed. 56 other passes do not establish the missing case or complete acceptance.|

## Commands for a configured local recovery copy
From the repository root, with Python 3.12 and pytest 9.0.0 already available:

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = '1'
$env:PYTHONPATH = "$PWD;$PWD/moriq/brain/experimental/source_gate"
python -B -m pytest --collect-only -q -p no:cacheprovider offline_integration/test_backend.py
python -B -m pytest -q --tb=short -p no:cacheprovider offline_integration/test_backend.py
```

These commands require local-only integration files excluded from the first documentation commit. Verify the interpreter and use writable temporary storage. The investigation used an observer plugin only to record collection lengths; it did not rename, deselect or modify tests. Exact launcher arguments, collection metadata, XML, logs and a standalone environment probe are retained in the local publication-review package. The previous migration launcher independently reproduced the same result.

## Recommended separate reviewed correction
After separate authorization, consider short explicit pytest parameter IDs while preserving every payload, assertion, fixture and acceptance ID. Do not shorten the oversized payload, skip the case, clear PYTEST_CURRENT_TEST through a bypass, weaken expectations, or declare a pass from this analysis. Re-run the unchanged semantic cases and applicable regressions after any approved labeling-only correction. No such correction was performed here.
