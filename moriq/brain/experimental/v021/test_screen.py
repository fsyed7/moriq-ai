"""Check isolation guards and preservation of partial stream output without inference."""

import importlib.util
import io
import json
import time
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('instruct_screen', Path(__file__).with_name('screen.py'))
screen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(screen)


class ScreenTests(unittest.TestCase):
    def test_rejects_competing_model_or_gpu(self):
        screen.check_loaded([])
        screen.check_loaded([{'name': screen.MODEL, 'size_vram': 0}])
        for models in (
            [{'name': 'qwen3:4b', 'size_vram': 0}],
            [{'name': screen.MODEL, 'size_vram': 1}],
            [{'name': screen.MODEL, 'size_vram': 0}] * 2,
        ):
            with self.assertRaises(RuntimeError):
                screen.check_loaded(models)

    def test_refuses_unapproved_matrix_size(self):
        with self.assertRaises(ValueError):
            screen.validate_plan([])

    def test_stream_failure_preserves_partial_answer(self):
        chunks = [{'message': {'content': 'Partial answer'}}, {'error': 'provider failed'}]
        stream = io.BytesIO(('\n'.join(json.dumps(c) for c in chunks)).encode())
        record = {'answer': '', 'thinking': '', 'tool_calls': [], 'transport_complete': False}
        with patch.object(screen, 'api', return_value=stream):
            with self.assertRaisesRegex(RuntimeError, 'provider failed'):
                screen.receive({'request': {}}, record, time.monotonic(), [])
        self.assertEqual(record['answer'], 'Partial answer')
        self.assertFalse(record['transport_complete'])


if __name__ == '__main__':
    unittest.main()
