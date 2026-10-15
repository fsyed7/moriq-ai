"""Additional offline race/metadata regressions; separate from frozen contract."""

import datetime as dt
import json
import threading
import unittest
from dataclasses import replace
from unittest.mock import Mock

from boundary import OfflinePrototype
from gateway import Document, Draft


class EdgeTests(unittest.TestCase):
    def setUp(self):
        self.today = dt.date.today()
        self.model = Mock(return_value=Draft('PRIVATE [4]', ('4',)))
        self.app = OfflinePrototype(
            {'a': ('author', {'author'}), 'b': ('reviewer', {'reviewer'})}, self.model, clock=lambda: self.today
        )
        self.args = dict(
            document=Document('4', 'Private source'),
            question='What is required by Ontario code?',
            kind='code',
            provenance='fixture publisher',
            applicability='fixture scope',
            jurisdiction='fixture jurisdiction',
            edition='fixture edition',
            expires_on=self.today + dt.timedelta(days=1),
        )

    def approve(self):
        key = self.app.create('a', **self.args)
        self.app.approve('b', key)
        return key

    def request(self, key):
        return self.app.public(json.dumps({'question': self.args['question'], 'attestation_ids': [key]}))

    def test_malformed_proposals(self):
        for field, value in [
            ('document', {'id': '4', 'approved': True}),
            ('question', ''),
            ('expires_on', '2099-01-01'),
            ('provenance', None),
            ('jurisdiction', ''),
            ('edition', ''),
            ('kind', 'approved'),
            ('document', Document('04', 'text')),
        ]:
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                self.app.create('a', **(self.args | {field: value}))
        self.assertEqual(self.app.audit('b'), ())

    def test_reviewer_inspection_and_authorization_of_every_operation(self):
        key = self.approve()
        for call in [
            lambda: self.app.inspect(None, key),
            lambda: self.app.audit(None),
            lambda: self.app.revoke(None, key),
            lambda: self.app.supersede(None, key, key),
        ]:
            with self.assertRaises(PermissionError):
                call()
        record = self.app.inspect('b', key)
        self.assertEqual(record.question, self.args['question'])
        self.assertEqual(record.review.reviewer, 'reviewer')
        with self.assertRaises(Exception):
            record.document.text = 'changed'

    def test_all_binding_fields_are_integrity_protected(self):
        key = self.approve()
        original, seal = self.app._records[key]
        for change in [
            replace(original, state='pending'),
            replace(original, question='changed'),
            replace(original, creator='other'),
            replace(original, version=999),
            replace(original, review=replace(original.review, edition='changed')),
            replace(original, review=replace(original.review, source_id='99')),
            replace(original, review=replace(original.review, expires_on=self.today)),
        ]:
            self.app._records[key] = (change, seal)
            self.assertEqual(json.loads(self.request(key))['status'], 'error')
        self.model.assert_not_called()

    def test_threaded_revocation_and_expiry_during_generation(self):
        for change in ['revoke', 'expire', 'supersede']:
            with self.subTest(change=change):
                self.setUp()
                key = self.approve()
                successor = self.approve()
                started, resume = threading.Event(), threading.Event()

                def generate(_):
                    started.set()
                    if not resume.wait(3):
                        raise RuntimeError('Test watchdog expired')
                    return Draft('PRIVATE stale [4]', ('4',))

                self.model.side_effect = generate
                responses = []
                thread = threading.Thread(target=lambda: responses.append(self.request(key)))
                thread.start()
                try:
                    self.assertTrue(started.wait(3))
                    if change == 'revoke':
                        self.app.revoke('b', key)
                    elif change == 'supersede':
                        self.app.supersede('b', key, successor)
                    else:
                        self.today += dt.timedelta(days=2)
                finally:
                    resume.set()
                    thread.join(3)
                self.assertFalse(thread.is_alive())
                self.assertEqual(json.loads(responses[0])['status'], 'source_gap')
                self.assertEqual(json.loads(self.app.view('b')), [])

    def test_previously_held_draft_removed_after_supersession(self):
        old, new = self.approve(), self.approve()
        self.request(old)
        self.assertIn('PRIVATE', self.app.view('b'))
        self.app.supersede('b', old, new)
        self.assertEqual(json.loads(self.app.view('b')), [])

    def test_replaying_old_valid_seal_cannot_undo_revocation(self):
        key = self.approve()
        previous = self.app._records[key]
        self.app.revoke('b', key)
        self.app._records[key] = previous
        self.assertEqual(json.loads(self.request(key))['status'], 'error')
        self.model.assert_not_called()


if __name__ == '__main__':
    unittest.main()
