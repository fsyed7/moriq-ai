"""Bounded mock-only subprocess harness; never constructs a live provider client."""

import hashlib
import json
import math
import os
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

from boundary import RESPONSES, OfflinePrototype, unique_object
from gateway import Draft

BUSY = '{"status":"busy","message":"Another request is active."}'
STOPPED = '{"status":"stopped","message":"Batch stopped. No answer released."}'
SCENARIOS = frozenset(
    {
        'success',
        'block',
        'slow',
        'delayed',
        'crash',
        'exception',
        'noise',
        'stderr',
        'large_stdout',
        'large_stderr',
        'raw',
        'partial',
        'partial_error',
        'network_guard',
        'environment',
    }
)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False)


def drain(pipe, buffer, limit, overflow, failed_io):
    try:
        while True:
            chunk = pipe.read(4096)
            if not chunk:
                break
            remaining = limit - len(buffer)
            buffer.extend(chunk[:remaining])
            if len(chunk) > remaining:
                overflow.set()
                break
    except Exception:
        failed_io.set()


def send(pipe, encoded, failed_io):
    try:
        pipe.write(encoded)
        pipe.close()
    except Exception:
        failed_io.set()


def reap(process, threads):
    # Kill and reap the process; a Python timeout alone would leave the callback alive.
    if process.poll() is None:
        process.kill()
    process.wait(timeout=2)
    for thread in threads:
        if thread.ident is not None:
            thread.join(timeout=1)
    if any(t.is_alive() for t in threads):
        raise RuntimeError('Worker pipe cleanup failed')
    for pipe in (process.stdin, process.stdout, process.stderr):
        pipe.close()


class MockHarness:
    def __init__(self, manifest_json, expected_sha256, credentials):
        if type(manifest_json) is not str or len(manifest_json.encode('utf-8')) > 1048576:
            raise ValueError('Invalid manifest')
        if hashlib.sha256(manifest_json.encode('utf-8')).hexdigest() != expected_sha256:
            raise ValueError('Manifest hash mismatch')
        manifest = json.loads(manifest_json, object_pairs_hook=unique_object)
        if (
            type(manifest) is not dict
            or set(manifest) != {'version', 'mode', 'model', 'endpoint', 'tools', 'options', 'count', 'cases'}
            or type(manifest['version']) is not int
            or manifest['version'] != 1
            or manifest['mode'] != 'mock'
            or manifest['model'] != 'deterministic-fake-v1'
            or manifest['endpoint'] is not None
            or manifest['tools'] != []
        ):
            raise ValueError('Only fixed mock configuration is supported')
        options = manifest['options']
        if (
            type(options) is not dict
            or set(options) != {'deadline_seconds'}
            or type(options['deadline_seconds']) not in (int, float)
            or not math.isfinite(options['deadline_seconds'])
            or not 0.05 <= options['deadline_seconds'] <= 5
        ):
            raise ValueError('Invalid deadline')
        cases = manifest['cases']
        if (
            type(cases) is not list
            or type(manifest['count']) is not int
            or not 1 <= len(cases) <= 16
            or manifest['count'] != len(cases)
        ):
            raise ValueError('Invalid batch size')
        for row in cases:
            if (
                type(row) is not dict
                or set(row) != {'request', 'scenario', 'reply'}
                or type(row['scenario']) is not str
                or row['scenario'] not in SCENARIOS
                or type(row['reply']) is not str
                or type(row['request']) is not dict
                or len(canonical(row).encode('utf-8')) > 65536
            ):
                raise ValueError('Invalid fixture')
        self._cases = cases
        self._deadline = options['deadline_seconds']
        self._flight = threading.Lock()
        self._state = threading.Lock()
        self._cancel = threading.Event()
        self._stopped = threading.Event()
        self._index = 0
        self._row = None
        self._process = None
        self.last_process = None  # trusted test diagnostics only; no response data
        self.started = threading.Event()
        self.launches = 0
        self.reviewer = OfflinePrototype(credentials, self._generate)

    def cancel(self):
        """Trusted operator action. Accepted only while the worker is still running."""
        with self._state:
            if self._process is None or self._process.poll() is not None:
                return False
            self._cancel.set()
            self._stopped.set()
            return True

    def public(self, payload):
        if not self._flight.acquire(blocking=False):
            return BUSY
        try:
            if self._stopped.is_set() or self._index >= len(self._cases):
                return STOPPED
            if type(payload) is not str or len(payload.encode('utf-8')) > 65536:
                raise ValueError('Invalid input')
            request = json.loads(payload, object_pairs_hook=unique_object)
            self._row = self._cases[self._index]
            if canonical(request) != canonical(self._row['request']):
                raise ValueError('Request not in approved manifest')
            self._index += 1
            result = self.reviewer.public(payload)
            if result not in RESPONSES.values():
                raise ValueError('Invalid public response')
            if json.loads(result)['status'] not in {'source_gap', 'review_required'}:
                self._stopped.set()
            return result
        except Exception:
            self._stopped.set()
            return RESPONSES['error']
        finally:
            self._row = None
            self._flight.release()

    def _generate(self, request):
        try:
            return self._run_worker(request)
        except Exception:
            self._stopped.set()
            raise RuntimeError('Mock generation failed') from None

    def _run_worker(self, request):
        encoded = canonical(
            {'request': request, 'scenario': self._row['scenario'], 'reply': self._row['reply']}
        ).encode('utf-8')
        if len(encoded) > 65536:
            raise ValueError('Oversized worker input')
        deadline = time.monotonic() + self._deadline
        env = {k: os.environ[k] for k in ('SYSTEMROOT', 'WINDIR') if k in os.environ}
        flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        process = subprocess.Popen(
            [sys.executable, '-I', '-u', str(Path(__file__).with_name('mock_worker.py'))],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            shell=False,
            close_fds=True,
            creationflags=flags,
        )
        with self._state:
            self._process = self.last_process = process
            self.launches += 1
            self.started.set()
        overflow = threading.Event()
        failed_io = threading.Event()
        buffers = [bytearray(), bytearray()]

        threads = [
            threading.Thread(target=drain, args=(process.stdout, buffers[0], 65536, overflow, failed_io), daemon=True),
            threading.Thread(target=drain, args=(process.stderr, buffers[1], 16384, overflow, failed_io), daemon=True),
            threading.Thread(target=send, args=(process.stdin, encoded, failed_io), daemon=True),
        ]
        try:
            for thread in threads:
                thread.start()
            while process.poll() is None or any(t.is_alive() for t in threads):
                if self._cancel.is_set() or overflow.is_set() or failed_io.is_set() or time.monotonic() >= deadline:
                    raise RuntimeError('Worker aborted')
                self._cancel.wait(0.005)
            with self._state:
                if self._cancel.is_set() or overflow.is_set() or failed_io.is_set() or time.monotonic() >= deadline:
                    raise RuntimeError('Worker aborted')
                self._process = None
            if process.returncode != 0 or buffers[1]:
                raise ValueError('Worker failed')
            reply = json.loads(buffers[0].decode('utf-8'), object_pairs_hook=unique_object)
            if (
                type(reply) is not dict
                or set(reply) != {'done', 'text'}
                or reply['done'] is not True
                or type(reply['text']) is not str
            ):
                raise ValueError('Incomplete worker reply')
            text = reply['text']
            ids = tuple(dict.fromkeys(re.findall(r'\[([1-9][0-9]*)\]', text)))
            if time.monotonic() >= deadline:
                raise RuntimeError('Reply arrived too late')
            return Draft(text, ids)
        finally:
            reap(process, threads)
            with self._state:
                self._process = None
