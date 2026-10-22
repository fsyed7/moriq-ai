"""Test-only isolation and bounded output scanner, shared by both lanes."""

import base64
import hashlib
import json
import os
import socket
import subprocess
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path
from unittest.mock import Mock

import pytest

from offline_evaluation.fixtures import SPEC

MARKER = SPEC['global_contracts_v2']['held_fixture']['marker']
H = SPEC['global_contracts_v2']['held_fixture']['text']
PATTERNS = {H, MARKER, *[MARKER[i : i + 8] for i in range(len(MARKER) - 7)]}
ENCODED = {
    encoded
    for text in PATTERNS
    for encoded in (
        text.encode(),
        json.dumps(text)[1:-1].encode(),
        urllib.parse.quote(text, safe='').encode(),
        base64.b64encode(text.encode()),
    )
}


def no_leak(value):
    raw = value if isinstance(value, bytes) else value.encode()
    assert not any(p in raw for p in ENCODED), 'Protected fixture output detected'


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.failed:
        # Fail fast without copying exception arguments, held text or frame locals to artifacts.
        category = call.excinfo.type.__name__ if call.excinfo else 'UnknownFailure'
        report.longrepr = f'{item.nodeid}: {report.when} failed ({category}); inspect the pinned assertion locally.'
        item.session.shouldstop = 'Evaluation gate failed; preserve evidence before further execution.'


def observe_call(original, counts):

    def call(*args, **kwargs):
        try:
            result = original(*args, **kwargs)
        except Exception as exc:
            counts[json.dumps({'operation': original.__name__, 'exception': type(exc).__name__}, sort_keys=True)] += 1
            raise
        event = {'operation': original.__name__, 'type': type(result).__name__}
        if hasattr(result, 'status'):
            event.update(
                status=result.status,
                reason=result.reason,
                claim_status=result.claim_status,
                release_allowed=result.release_allowed,
            )
        if hasattr(result, 'hits'):
            event['chunks'] = [h.chunk.chunk_id for h in result.hits]
        if type(result) is bytes:
            event['status'] = json.loads(result)['status']
        counts[json.dumps(event, sort_keys=True)] += 1
        return result

    return call


@pytest.fixture(autouse=True)
def isolation(monkeypatch, capsys):
    repo = Path(__file__).resolve().parents[1]
    hashes = json.loads(Path(__file__).with_name('runtime-hashes.json').read_bytes())
    assert all((hashlib.sha256((repo / name).read_bytes()).hexdigest() == want for name, want in hashes.items()))
    traps = []
    for owner, name in ((socket, 'socket'), (subprocess, 'Popen'), (urllib.request, 'urlopen'), (os, 'system')):
        trap = Mock(side_effect=AssertionError('Forbidden network/process operation'))
        monkeypatch.setattr(owner, name, trap)
        traps.append(trap)
    yield
    captured = capsys.readouterr()
    no_leak(captured.out)
    no_leak(captured.err)
    assert all(t.call_count == 0 for t in traps)
    assert all((hashlib.sha256((repo / name).read_bytes()).hexdigest() == want for name, want in hashes.items()))


@pytest.fixture(autouse=True)
def observations(request, monkeypatch, record_property):
    """Capture bounded public outcomes independently of frozen gold labels."""
    counts = Counter()
    module = request.module
    for name in ('retrieve', 'validate_references'):
        if hasattr(module, name):
            monkeypatch.setattr(module, name, observe_call(getattr(module, name), counts))
    if hasattr(module, 'kp'):
        for name in ('check', 'prepare'):
            cls = module.kp.OfflineKnowledgePreflight
            monkeypatch.setattr(cls, name, observe_call(getattr(cls, name), counts))
        for name in ('prepare', 'view_fixture', 'request_view', 'begin_fixture', 'create_request', 'update_request'):
            cls = module.life.OfflinePrivateDraftLifecycle
            monkeypatch.setattr(cls, name, observe_call(getattr(cls, name), counts))
    yield
    record_property('actual_outcomes', [{'outcome': json.loads(k), 'count': n} for k, n in sorted(counts.items())])
