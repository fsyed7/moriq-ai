"""Execute H01-H16 against real gate/boundary and isolated deterministic workers."""

import contextlib
import datetime as dt
import hashlib
import io
import json
import logging
import os
import socket
import threading
import time
import unittest
import urllib.request
from pathlib import Path
from unittest.mock import patch

from mock_harness import MockHarness, canonical

EDUCATION = 'What is an RCP?'
CODE = 'What does the Ontario code require for this project?'
TOKEN = 'SYNTHETIC_REVIEWER_TOKEN'
CREDENTIALS = {'author': ('alice', {'author'}), TOKEN: ('bob', {'reviewer'})}


def row(question=EDUCATION, scenario='success', reply='PRIVATE teaching', ids=()):
    return {'request': {'question': question, 'attestation_ids': list(ids)}, 'scenario': scenario, 'reply': reply}


def plan(rows, deadline=2):
    return {
        'version': 1,
        'mode': 'mock',
        'model': 'deterministic-fake-v1',
        'endpoint': None,
        'tools': [],
        'options': {'deadline_seconds': deadline},
        'count': len(rows),
        'cases': rows,
    }


def make(rows=None, deadline=2):
    rows = rows or [row()]
    raw = canonical(plan(rows, deadline))
    return MockHarness(raw, hashlib.sha256(raw.encode()).hexdigest(), CREDENTIALS)


class HarnessAcceptanceTests(unittest.TestCase):
    def public(self, harness, item):
        capture = io.StringIO()
        handler = logging.StreamHandler(capture)
        logging.getLogger().addHandler(handler)
        try:
            with contextlib.redirect_stdout(capture), contextlib.redirect_stderr(capture):
                result = harness.public(canonical(item['request']))
        finally:
            logging.getLogger().removeHandler(handler)
        self.assertEqual(capture.getvalue(), '')
        self.assertNotIn('PRIVATE', result)
        self.assertNotIn('review_draft', result)
        self.assertEqual(set(json.loads(result)), {'status', 'message'})
        return json.loads(result)['status']

    def approved(self, harness, key='1' * 32):
        from gateway import Document

        with patch('boundary.secrets.token_hex', return_value=key):
            actual = harness.reviewer.create(
                'author',
                document=Document('4', 'PRIVATE synthetic source'),
                question=CODE,
                provenance='Synthetic publisher',
                applicability='Synthetic scope',
                jurisdiction='Synthetic Ontario',
                edition='Synthetic edition',
                expires_on=dt.date.today() + dt.timedelta(days=1),
            )
        harness.reviewer.approve(TOKEN, actual)
        return actual

    def assert_dead(self, harness):
        self.assertIsNotNone(harness.last_process)
        self.assertIsNotNone(harness.last_process.poll())
        self.assertTrue(harness.last_process.stdout.closed)
        self.assertTrue(harness.last_process.stderr.closed)

    def test_H01_no_network(self):
        with (
            patch.object(socket, 'socket', side_effect=AssertionError('network')) as sock,
            patch.object(socket, 'create_connection', side_effect=AssertionError('network')) as connect,
            patch.object(urllib.request, 'urlopen', side_effect=AssertionError('network')) as http,
        ):
            item = row(scenario='network_guard')
            self.assertEqual(self.public(make([item]), item), 'review_required')
            sock.assert_not_called()
            connect.assert_not_called()
            http.assert_not_called()

    def test_H02_zero_call_source_gaps(self):
        rows = [
            row(q)
            for q in [
                CODE,
                'Would this pass the inspector?',
                'What is our company drawing policy?',
                'Explain an RCP and the legal sprinkler spacing',
            ]
        ]
        harness = make(rows)
        for item in rows:
            self.assertEqual(self.public(harness, item), 'source_gap')
        self.assertEqual(harness.launches, 0)
        self.assertIsNone(harness.last_process)

    def test_H03_public_error_and_success_sentinels(self):
        items = [
            row(),
            row(scenario='exception'),
            row(scenario='crash'),
            row(scenario='raw', reply='PRIVATE malformed path'),
            row(scenario='raw', reply='{"status":"PRIVATE","done":true,"text":"PRIVATE"}'),
        ]
        for item in items:
            with self.subTest(scenario=item['scenario'], reply=item['reply']):
                harness = make([item])
                self.public(harness, item)
                self.assert_dead(harness)

    def test_H04_native_and_python_output_isolation(self):
        for scenario in ['noise', 'stderr']:
            harness = make([row(scenario=scenario)])
            self.assertEqual(self.public(harness, row(scenario=scenario)), 'generation_failed')
            self.assertEqual(harness.reviewer.view(TOKEN), '[]')
            self.assert_dead(harness)

    def test_H05_parser_and_size_bounds(self):
        raw = [
            '{}',
            'null',
            '[]',
            '{"done":true,"text":42}',
            '{"done":true,"text":"PRIVATE","text":"PRIVATE"}',
            '{"done":true,"text":"PRIVATE"}{}',
            '{"done":true,"text":"PRIVATE"}PRIVATE trailing',
        ]
        items = [row(scenario='raw', reply=r) for r in raw]
        items += [row(scenario='large_stdout'), row(scenario='large_stderr')]
        for item in items:
            harness = make([item])
            self.assertEqual(self.public(harness, item), 'generation_failed')
            self.assertEqual(harness.reviewer.view(TOKEN), '[]')
            self.assert_dead(harness)
        harness = make()
        self.assertEqual(json.loads(harness.public('X' * 65537))['status'], 'error')
        self.assertEqual(harness.launches, 0)

    def test_H06_partial_streams_never_become_drafts(self):
        items = [
            row(scenario='partial'),
            row(scenario='partial_error'),
            row(scenario='raw', reply='{"done":false,"text":"PRIVATE"}'),
            row(scenario='raw', reply='{"text":"PRIVATE"}'),
            row(scenario='raw', reply='{"done":true,"text":"PRIVATE","tools":["exec"]}'),
        ]
        for item in items:
            harness = make([item])
            self.assertEqual(self.public(harness, item), 'generation_failed')
            self.assertEqual(harness.reviewer.view(TOKEN), '[]')
            self.assert_dead(harness)

    def test_H07_cancel_terminates_and_latches(self):
        item = row(scenario='block')
        harness = make([item, item])
        results = []
        thread = threading.Thread(target=lambda: results.append(harness.public(canonical(item['request']))))
        thread.start()
        try:
            self.assertTrue(harness.started.wait(2))
            self.assertTrue(harness.cancel())
        finally:
            thread.join(4)
        self.assertFalse(thread.is_alive())
        self.assertEqual(json.loads(results[0])['status'], 'generation_failed')
        self.assert_dead(harness)
        self.assertEqual(self.public(harness, item), 'stopped')
        self.assertEqual(harness.launches, 1)
        self.assertEqual(harness.reviewer.view(TOKEN), '[]')

    def test_H08_deadlines_ignore_read_activity_and_late_completion(self):
        for scenario in ['block', 'slow', 'delayed']:
            item = row(scenario=scenario)
            harness = make([item, item], deadline=0.1)
            started = time.monotonic()
            self.assertEqual(self.public(harness, item), 'generation_failed')
            self.assertLess(time.monotonic() - started, 4)
            self.assert_dead(harness)
            self.assertEqual(harness.reviewer.view(TOKEN), '[]')
            self.assertEqual(self.public(harness, item), 'stopped')

    def test_H09_single_flight_no_queue(self):
        item = row(scenario='block')
        harness = make([item, item])
        results = []
        thread = threading.Thread(target=lambda: results.append(harness.public(canonical(item['request']))))
        thread.start()
        try:
            self.assertTrue(harness.started.wait(2))
            self.assertEqual(self.public(harness, item), 'busy')
            self.assertEqual(harness.launches, 1)
        finally:
            harness.cancel()
            thread.join(4)
        self.assertFalse(thread.is_alive())
        self.assert_dead(harness)
        self.assertEqual(harness.launches, 1)

    def test_H10_reviewer_auth_before_serialization(self):
        harness = make()
        self.assertEqual(self.public(harness, row()), 'review_required')
        with patch('boundary.json.dumps', side_effect=AssertionError('PRIVATE serialization')) as dump:
            for token in [None, 'author', 'wrong', {'role': 'reviewer'}]:
                with self.assertRaises(PermissionError):
                    harness.reviewer.view(token)
            dump.assert_not_called()
        self.assertIn('PRIVATE teaching', harness.reviewer.view(TOKEN))
        self.assertEqual(json.loads(harness.public('{"view":true}'))['status'], 'stopped')

    def test_H11_attestation_changes_during_worker(self):
        for action in ['revoke', 'expire', 'supersede']:
            item = row(CODE, 'delayed', 'PRIVATE claim [4]', ['1' * 32])
            harness = make([item])
            self.approved(harness)
            if action == 'supersede':
                self.approved(harness, '2' * 32)
            results = []
            thread = threading.Thread(target=lambda: results.append(harness.public(canonical(item['request']))))
            thread.start()
            try:
                self.assertTrue(harness.started.wait(2))
                if action == 'revoke':
                    harness.reviewer.revoke(TOKEN, '1' * 32)
                elif action == 'supersede':
                    harness.reviewer.supersede(TOKEN, '1' * 32, '2' * 32)
                else:
                    harness.reviewer._clock = lambda: dt.date.today() + dt.timedelta(days=2)
            finally:
                thread.join(4)
            self.assertFalse(thread.is_alive())
            self.assertEqual(json.loads(results[0])['status'], 'source_gap')
            self.assertEqual(harness.reviewer.view(TOKEN), '[]')
            self.assert_dead(harness)

    def test_H12_citations_are_not_repaired_or_fact_checks(self):
        for reply in ['PRIVATE missing', 'PRIVATE wrong [99]', 'PRIVATE [4](javascript:x)', 'PRIVATE false claim [4]']:
            item = row(CODE, reply=reply, ids=['1' * 32])
            harness = make([item])
            self.approved(harness)
            expected = 'review_required' if reply == 'PRIVATE false claim [4]' else 'citation_blocked'
            self.assertEqual(self.public(harness, item), expected)
            if expected == 'citation_blocked':
                self.assertEqual(harness.reviewer.view(TOKEN), '[]')
            else:
                self.assertIn('PRIVATE false claim', harness.reviewer.view(TOKEN))

    def test_H13_manifest_rejects_changed_configuration(self):
        original = canonical(plan([row()]))
        hashed = hashlib.sha256(original.encode()).hexdigest()
        with patch('mock_harness.subprocess.Popen') as launch:
            with self.assertRaises(ValueError):
                MockHarness(original + ' ', hashed, CREDENTIALS)
            for field, value in [
                ('count', 2),
                ('mode', 'live'),
                ('model', 'qwen3'),
                ('endpoint', 'http://127.0.0.1:11434'),
                ('tools', ['exec']),
                ('options', {'num_gpu': 1}),
            ]:
                bad = plan([row()]) | {field: value}
                raw = canonical(bad)
                with self.assertRaises(ValueError):
                    MockHarness(raw, hashlib.sha256(raw.encode()).hexdigest(), CREDENTIALS)
            launch.assert_not_called()
        harness = make()
        self.assertEqual(
            json.loads(harness.public('{"question":"What is an RCP?","scenario":"live"}'))['status'], 'error'
        )
        self.assertEqual(harness.launches, 0)

    def test_H14_credentials_not_in_child_and_no_raw_exports(self):
        item = row(scenario='environment')
        with patch.dict(os.environ, {'MORIQ_SECRET': 'PRIVATE_SECRET', 'REVIEW_TOKEN': TOKEN}):
            harness = make([item])
            self.assertEqual(self.public(harness, item), 'review_required')
        self.assertFalse(hasattr(harness, 'export'))
        self.assertNotIn(TOKEN, str(harness.last_process.args))
        self.assertNotIn(harness.reviewer._key.hex(), str(harness.last_process.args))
        self.assert_dead(harness)

    def test_H15_prior_evidence_and_frozen_checklist(self):
        here = Path(__file__).parent
        repo = here.parents[3]
        hashes = json.loads((here / 'lifecycle_evidence/prior-hashes.json').read_text(encoding='utf-8'))
        self.assertEqual(len(hashes), 67)
        for relative, expected in hashes.items():
            self.assertEqual(hashlib.sha256((repo / relative).read_bytes()).hexdigest(), expected)
        frozen = json.loads((here / 'task37_evidence/frozen-design-hashes.json').read_text(encoding='utf-8'))
        for name, expected in frozen.items():
            self.assertEqual(hashlib.sha256((here / name).read_bytes()).hexdigest(), expected)

    def test_H16_no_live_mode_even_with_matching_manifest_hash(self):
        for mode in ['live', 'ollama', 'api', True]:
            raw = canonical(plan([row()]) | {'mode': mode})
            with self.assertRaises(ValueError):
                MockHarness(raw, hashlib.sha256(raw.encode()).hexdigest(), CREDENTIALS)

    def test_overdue_reply_parsing_is_discarded(self):
        harness = make(deadline=0.5)
        original = json.loads

        def delayed_parse(value, *args, **kwargs):
            if isinstance(value, str) and value.startswith('{"done":'):
                time.sleep(0.6)
            return original(value, *args, **kwargs)

        with patch('mock_harness.json.loads', side_effect=delayed_parse):
            self.assertEqual(self.public(harness, row()), 'generation_failed')
        self.assertEqual(harness.reviewer.view(TOKEN), '[]')
        self.assert_dead(harness)

    def test_invalid_attestations_never_launch_worker(self):
        from dataclasses import replace

        for change in ['revoked', 'expired', 'tampered', 'substituted', 'replayed']:
            item = row(CODE, reply='PRIVATE claim [4]', ids=['1' * 32])
            harness = make([item])
            key = self.approved(harness)
            record, seal = harness.reviewer._records[key]
            if change == 'revoked':
                harness.reviewer.revoke(TOKEN, key)
            elif change == 'expired':
                harness.reviewer._clock = lambda: dt.date.today() + dt.timedelta(days=2)
            elif change == 'tampered':
                harness.reviewer._records[key] = (replace(record, question='PRIVATE tampered'), seal)
            elif change == 'substituted':
                second = self.approved(harness, '2' * 32)
                harness.reviewer._records[key] = harness.reviewer._records[second]
            else:
                harness.reviewer.revoke(TOKEN, key)
                harness.reviewer._records[key] = (record, seal)
            self.assertIn(self.public(harness, item), {'error', 'source_gap'})
            self.assertEqual(harness.launches, 0)


if __name__ == '__main__':
    unittest.main()
