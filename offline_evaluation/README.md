# E46-v2 isolated offline evaluation

Synthetic evaluation only. This package does not add an application endpoint,
change retrieval behavior, invoke a model, or grant real-source approval.
The frozen original remains outside this repository. `e46-v2.json` is an exact
copy of the approved corrected specification, SHA-256
`4be7da6705b917b58a74230b374abb032444c4901816f5b447c8f0b5957ac9b7`.

Run the registry and authority test modules in separate Python processes with
the repository on `PYTHONPATH`. The authority process additionally needs
`moriq/brain/experimental/source_gate` and `synthetic_pilot` on its import path.
Use installed pytest, `-p no:cacheprovider`, `PYTHONDONTWRITEBYTECODE=1`, and write
JUnit files outside the repository. Do not collect historical evidence copies.
The external `work/run46b.py` launcher records the exact selections used here.

The 113 executable frozen variants comprise 83 registry/metric variants and
30 authority variants. E23 is the combined isolation/integrity gate, E24 is the
nine-worker benchmark gate, and E25 is the unchanged regression/integrity gate.
They are three additional frozen variants, not three invented pytest passes.
Two supplemental registry checks cover lane isolation and leakage-detector
oracles; neither increases the 54-case/116-variant frozen counts.

`fixtures.py` provisions literal synthetic records using independent test roles.
Gold rankings are assertions only; they never enter application ranking calls.
Original text, metadata, hashes, identities, offsets, and lifecycle are checked.
`metrics.py` defines pure arithmetic and is checked against E26 hand oracles.
The v2 specification retains all original case/variant IDs and expectations.

New authority tests reuse original helper setup, not the historical test bodies.
Their clocks are fixed to the v2 dates. Six roles remain distinct. Existing
Task3 generator/private-view regressions run unchanged in separate processes.
Only the existing synthetic fixture-copy API is used by this new authority lane.

The generic lifecycle denial is insufficient evidence by itself. A delegated
`require` observer identifies the exact failing predicate by function and
source-order guard number. Runtime file hashes are pinned. Exception observation
records categories only, including worker threads; it never captures arguments,
locals or held text. Paired positives prove the observer preserves output.
The registry corruption observer verifies the exact original raise site.
Race tests observe actual writer admission with events and the original lock,
not sleeps. Unexpected test failures stop execution and suppress sensitive
exception details from reports; inspect the pinned assertion locally.

Network/process tripwires, source hash checks, generator/viewer tripwires, fixed
public schemas, and a held-only canary scanner protect the isolated test lanes.
Authorized fixture copies are excluded from leakage counting. Minimum scanner
coverage is full text/marker and eight-character marker fragments in literal,
JSON-escaped, percent-encoded and base64 representations. This is not a proof
against arbitrary encodings, short fragments, side channels or a malicious host.

For each benchmark profile, run three sequential fresh processes:

```text
python -B -m offline_evaluation.benchmark small 1 ABSOLUTE_OUTPUT_JSON
```

Profiles are `small`, `medium`, `byte-limit`; runs are 1, 2, 3. The external
`work/bench46b.py` supervisor imposes the collective 30-minute deadline.
Each process constructs its corpus before measuring 10 warmups, 100 alternating
hit/gap timings, then 20 separate traced allocation calls. Latency excludes setup,
serialization and tracing. Incremental peak is P-B; current C is diagnostic only.
Report every raw sample and every per-run hit/gap p95. No pooled gate substitute.

Interpretation limits: Q05 is literal topical relevance only. D01-D05 and E09
retain uncovered semantic capabilities. Citations do not prove claims. The code
preflight still refuses educational fixtures. Identity, audit, leases and locking
assume one trusted, volatile host. No durable or cross-process security, real
architectural authority, production performance, or model factuality is established.
Unapproved notes and C01 are not inputs. No source approval, commit or deployment
is authorized by a passing evaluation.
