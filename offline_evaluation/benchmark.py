"""Bounded synthetic retrieval measurement in one fresh worker process."""

import argparse
import datetime as dt
import hashlib
import json
import os
import platform
import sys
import time
import tracemalloc
from dataclasses import asdict
from pathlib import Path

from moriq.knowledge.retrieval import retrieve
from offline_evaluation.fixtures import Date, Time, corpus, observed
from offline_evaluation.metrics import allocation, quantiles

PROFILES = {'small': (10, 1200, 10), 'medium': (50, 12000, 500), 'byte-limit': (100, 100000, 8400)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('profile', choices=PROFILES)
    parser.add_argument('run', type=int, choices=(1, 2, 3))
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    dt.date = Date
    dt.datetime = Time
    n, size, count = PROFILES[args.profile]
    r = corpus(n, size)
    chunks = r.snapshot()[1]
    assert len(chunks) == count and sum(len(c.text.encode()) for c in chunks) == n * size
    ledger = [asdict(v) for v in r._records.values()]
    fixture_hash = hashlib.sha256(json.dumps(ledger, sort_keys=True).encode()).hexdigest()
    del chunks, ledger
    digests = {}

    def check(result, stratum):
        assert result.status == ('passages' if stratum == 'hit' else 'evidence_gap')
        assert not result.release_allowed and result.claim_status == 'not_assessed'
        value = hashlib.sha256(json.dumps(observed(result), sort_keys=True).encode()).hexdigest()
        assert digests.setdefault(stratum, value) == value
        return value

    for i in range(10):
        stratum = 'hit' if i % 2 == 0 else 'gap'
        result = retrieve('thermal bridge' if stratum == 'hit' else 'seismic joint', r)
        check(result, stratum)
    del result
    timed = []
    for i in range(100):
        stratum = 'hit' if i % 2 == 0 else 'gap'
        query = 'thermal bridge' if stratum == 'hit' else 'seismic joint'
        start = time.perf_counter_ns()
        result = retrieve(query, r)
        elapsed = time.perf_counter_ns() - start
        timed.append(dict(sample=i, stratum=stratum, elapsed_ns=elapsed, result_digest=check(result, stratum)))
        del result
    memory = []
    for i in range(20):
        stratum = 'hit' if i % 2 == 0 else 'gap'
        query = 'thermal bridge' if stratum == 'hit' else 'seismic joint'
        tracemalloc.start()
        baseline = tracemalloc.get_traced_memory()[0]
        tracemalloc.reset_peak()
        result = retrieve(query, r)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        increment = allocation(baseline, current, peak)
        memory.append(
            dict(
                sample=i,
                stratum=stratum,
                baseline_bytes=baseline,
                current_bytes=current,
                peak_bytes=peak,
                incremental_bytes=increment,
                result_digest=check(result, stratum),
            )
        )
        del result
    latency = {
        s: quantiles([x['elapsed_ns'] / 1e9 for x in timed if s == 'mixed' or x['stratum'] == s])
        for s in ('hit', 'gap', 'mixed')
    }
    report = dict(
        profile=args.profile,
        run=args.run,
        documents=n,
        bytes_per_document=size,
        total_bytes=n * size,
        chunks=count,
        environment=dict(
            python=sys.version,
            executable=sys.executable,
            platform=platform.platform(),
            processor=platform.processor(),
            logical_cpus=os.cpu_count(),
            memory_availability='UNKNOWN',
            power_mode='UNKNOWN',
        ),
        fixture_sha256=fixture_hash,
        warmups=10,
        timed=timed,
        allocation=memory,
        latency=latency,
        passed=all(latency[s]['p95'] <= 1 for s in ('hit', 'gap'))
        and all(x['incremental_bytes'] <= 134217728 for x in memory),
    )
    raw = json.dumps(report, indent=2).encode()
    assert len(raw) <= 10000000
    args.output.write_bytes(raw + b'\n')
    print(json.dumps(dict(profile=args.profile, run=args.run, passed=report['passed'], latency=latency)))


if __name__ == '__main__':
    main()
