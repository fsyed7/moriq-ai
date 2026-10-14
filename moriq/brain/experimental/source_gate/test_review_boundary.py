"""Focused regression tests for the new out-of-band reviewer handoff."""

import json
import unittest
from dataclasses import asdict
from unittest.mock import Mock

from gateway import Draft, Gateway


class ReviewBoundaryTests(unittest.TestCase):
    def test_private_sink_receives_draft_public_result_does_not(self):
        held = []
        result = Gateway(review_sink=held.append).respond(
            'Explain an RCP in plain English.', generate=lambda _: Draft('PRIVATE_REVIEW_TEXT')
        )
        self.assertEqual(held[0].draft.text, 'PRIVATE_REVIEW_TEXT')
        self.assertEqual(set(asdict(result)), {'status', 'route', 'answer'})
        self.assertNotIn('PRIVATE_REVIEW_TEXT', json.dumps(asdict(result)))
        self.assertNotIn('PRIVATE_REVIEW_TEXT', repr(result))
        self.assertNotIn('PRIVATE_REVIEW_TEXT', repr(held[0]))
        self.assertFalse(hasattr(result, '__dict__'))

    def test_no_sink_discards_draft(self):
        result = Gateway().respond('What is an RCP?', generate=lambda _: Draft('PRIVATE_REVIEW_TEXT'))
        self.assertIn('discarded', result.answer)
        self.assertNotIn('PRIVATE_REVIEW_TEXT', repr(result))

    def test_sink_failure_does_not_echo_exception_or_draft(self):
        sink = Mock(side_effect=RuntimeError('PRIVATE_REVIEW_TEXT'))
        result = Gateway(review_sink=sink).respond('What is an RCP?', generate=lambda _: Draft('PRIVATE_REVIEW_TEXT'))
        self.assertEqual(result.status, 'review_failed')
        self.assertNotIn('PRIVATE_REVIEW_TEXT', json.dumps(asdict(result)))

    def test_gap_and_bad_citation_never_reach_sink(self):
        sink = Mock()
        gate = Gateway(review_sink=sink)
        model = Mock(return_value=Draft('Unverified requirement'))
        gate.respond('What is legally required?', generate=model)
        model.assert_not_called()
        gate.respond('What is an RCP?', generate=lambda _: Draft('Fake reference [99]', ('99',)))
        sink.assert_not_called()

    def test_type_confused_exercise_configuration_is_rejected(self):
        with self.assertRaises(ValueError):
            Gateway(exercise='false')


if __name__ == '__main__':
    unittest.main()
