"""Independent offline review regressions; known failure retained, not xfailed."""

import contextlib
import datetime as dt
import io
import json
import unittest
from unittest.mock import Mock, patch

from boundary import OfflinePrototype
from gateway import Document, Draft, Result


class Task36ReviewTests(unittest.TestCase):
    def setUp(self):
        self.model = Mock(return_value=Draft('PRIVATE claim [4]', ('4',)))
        self.app = OfflinePrototype({'a': ('author', {'author'}), 'r': ('reviewer', {'reviewer'})}, self.model)
        self.question = 'What is required by the Ontario code for this project?'

    def approved(self, text):
        key = self.app.create(
            'a',
            document=Document('4', text),
            question=self.question,
            kind='code',
            provenance='Synthetic publisher',
            applicability='Synthetic scope',
            jurisdiction='Synthetic Ontario',
            edition='Synthetic edition',
            expires_on=dt.date.today() + dt.timedelta(days=1),
        )
        self.app.approve('r', key)
        return key

    def ask(self, key):
        return self.app.public(json.dumps({'question': self.question, 'attestation_ids': [key]}))

    def test_signed_record_cannot_be_transplanted_to_another_registry_id(self):
        first = self.approved('PRIVATE first source')
        second = self.approved('PRIVATE replacement source')
        # Storage-corruption injection, same fault surface as the existing replay test.
        # No token forgery, new signature, audit edit or hostile model execution.
        self.app._records[first] = self.app._records[second]
        response = self.ask(first)
        with self.subTest('fixed public response'):
            self.assertNotIn('PRIVATE', response)
        with self.subTest('reject wrong record identity'):
            self.assertEqual(json.loads(response)['status'], 'error')
        with self.subTest('reject before generation'):
            self.model.assert_not_called()

    def test_legitimate_signed_record_remains_usable(self):
        key = self.approved('PRIVATE source')
        self.assertEqual(json.loads(self.ask(key))['status'], 'review_required')
        self.assertEqual(self.model.call_count, 1)
        self.assertIn('PRIVATE claim', self.app.view('r'))

    def test_public_result_and_mock_generation_emit_no_private_stdout(self):
        key = self.approved('PRIVATE source')
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            response = self.ask(key)
        self.assertEqual(stdout.getvalue() + stderr.getvalue(), '')
        self.assertEqual(set(json.loads(response)), {'status', 'message'})
        self.assertNotIn('PRIVATE', response)

    def test_authorization_precedes_private_serialization(self):
        key = self.approved('PRIVATE source')
        self.ask(key)
        with patch('boundary.json.dumps', side_effect=RuntimeError('PRIVATE serializer')) as serializer:
            for token in [None, 'a', 'wrong', {'role': 'reviewer'}]:
                with self.assertRaises(PermissionError):
                    self.app.view(token)
            serializer.assert_not_called()

    def test_unknown_status_and_internal_result_text_are_never_echoed(self):
        for status in ['PRIVATE status', 'review_required', 'generation_failed']:
            with patch('boundary.Gateway.respond', return_value=Result(status, 'PRIVATE route', 'PRIVATE output')):
                response = self.app.public('{"question":"What is an RCP?"}')
            self.assertNotIn('PRIVATE', response)
            self.assertEqual(set(json.loads(response)), {'status', 'message'})

    def test_callback_stdout_is_outside_json_boundary_characterization(self):
        # This records a harness limitation, not a claim of a public JSON leak.
        def logging_callback(_):
            print('PRIVATE callback output')
            return Draft('PRIVATE answer')

        app = OfflinePrototype({}, logging_callback)
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            response = app.public('{"question":"What is an RCP?"}')
        self.assertNotIn('PRIVATE', response)
        self.assertIn('PRIVATE callback output', stdout.getvalue())


if __name__ == '__main__':
    unittest.main()
