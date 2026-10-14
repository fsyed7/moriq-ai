"""Registry identity and legacy-seal rejection; no live generation."""

import datetime as dt
import hashlib
import hmac
import json
import unittest
from dataclasses import asdict, replace
from unittest.mock import Mock

from boundary import OfflinePrototype
from gateway import Document, Draft


class RegistryBindingTests(unittest.TestCase):
    def setUp(self):
        self.model = Mock(return_value=Draft('PRIVATE claim [4]', ('4',)))
        self.app = OfflinePrototype({'a': ('author', {'author'}), 'r': ('reviewer', {'reviewer'})}, self.model)
        self.question = 'What does the Ontario code require?'

    def approved(self):
        key = self.app.create(
            'a',
            document=Document('4', 'Synthetic PRIVATE evidence'),
            question=self.question,
            provenance='Synthetic publisher',
            applicability='Synthetic scope',
            jurisdiction='Synthetic jurisdiction',
            edition='Synthetic edition',
            expires_on=dt.date.today() + dt.timedelta(days=1),
        )
        self.app.approve('r', key)
        return key

    def response(self, key):
        text = self.app.public(json.dumps({'question': self.question, 'attestation_ids': [key]}))
        self.assertNotIn('PRIVATE', text)
        self.assertEqual(set(json.loads(text)), {'status', 'message'})
        return json.loads(text)['status']

    def test_equal_version_equal_contents_distinct_identities_have_distinct_seals(self):
        first, second = self.approved(), self.approved()
        a, a_seal = self.app._records[first]
        b, b_seal = self.app._records[second]
        self.assertEqual(a.version, b.version)
        self.assertEqual(replace(a, registry_id=second), b)
        self.assertNotEqual(a_seal, b_seal)
        self.assertEqual(self.response(first), 'review_required')
        self.assertEqual(self.response(second), 'review_required')

    def test_missing_invalid_and_tampered_ids_fail_closed(self):
        key = self.approved()
        record, seal = self.app._records[key]
        for identity in [None, '', 'A' * 32, '0' * 32, 42, key + 'x']:
            with self.subTest(identity=identity):
                self.app._records[key] = (replace(record, registry_id=identity), seal)
                self.assertEqual(self.response(key), 'error')
        missing = replace(record)
        object.__delattr__(missing, 'registry_id')
        self.app._records[key] = (missing, seal)
        self.assertEqual(self.response(key), 'error')
        self.model.assert_not_called()

    def test_transplant_with_rewritten_identity_still_fails_mac(self):
        first, second = self.approved(), self.approved()
        record, seal = self.app._records[second]
        self.app._records[first] = (replace(record, registry_id=first), seal)
        self.assertEqual(self.response(first), 'error')
        self.model.assert_not_called()

    def test_legacy_seal_is_rejected_even_if_identity_was_added(self):
        key = self.approved()
        record, _ = self.app._records[key]
        legacy = asdict(record)
        del legacy['registry_id']
        old_bytes = json.dumps(legacy, sort_keys=True, default=str).encode('utf-8')
        old_seal = hmac.new(self.app._key, old_bytes, hashlib.sha256).hexdigest()
        self.app._records[key] = (record, old_seal)
        self.assertEqual(self.response(key), 'error')
        self.model.assert_not_called()

    def test_same_identity_replay_after_revocation_remains_rejected(self):
        key = self.approved()
        previous = self.app._records[key]
        self.app.revoke('r', key)
        self.app._records[key] = previous
        self.assertEqual(self.response(key), 'error')
        self.model.assert_not_called()

    def test_canonical_payload_and_rejection_before_signing(self):
        key = self.approved()
        record, seal = self.app._records[key]
        payload = asdict(record)
        for name in ('reviewed_on', 'expires_on'):
            payload['review'][name] = getattr(record.review, name).isoformat()
        encoded = json.dumps(
            {'format': 'moriq-attestation-v2', 'record': payload},
            sort_keys=True,
            separators=(',', ':'),
            ensure_ascii=True,
            allow_nan=False,
        ).encode('utf-8')
        self.assertEqual(seal, hmac.new(self.app._key, encoded, hashlib.sha256).hexdigest())
        for bad_key in [None, '', 'A' * 32, 'x' * 32, key + '\n']:
            with self.assertRaises(ValueError):
                self.app._seal(bad_key, record)
        with self.assertRaises(ValueError):
            self.app._seal(key, replace(record, review=replace(record.review, expires_on='2099-01-01')))


if __name__ == '__main__':
    unittest.main()
