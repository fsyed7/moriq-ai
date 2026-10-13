"""Isolation/reproducibility checks, not model answer-quality tests."""

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name):
    spec = importlib.util.spec_from_file_location('experimental_' + name, HERE / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ExperimentTests(unittest.TestCase):
    def test_artifact_is_disabled_private_and_separate(self):
        builder = load('build')
        ids = set()
        for model, mode in [('qwen3:4b', 'soft'), ('qwen3.5:2b', 'off')]:
            artifact = builder.build_model(model, mode)
            self.assertNotEqual(artifact['id'], 'moriq-ai')
            self.assertFalse(artifact['is_active'])
            self.assertEqual(artifact['access_grants'], [])
            self.assertFalse(artifact['meta']['capabilities']['builtin_tools'])
            self.assertNotIn('knowledge', artifact['meta'])
            ids.add(artifact['id'])
        self.assertEqual(len(ids), 2)

    def test_cli_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'import.json'
            command = [
                sys.executable,
                str(HERE / 'build.py'),
                '--base-model-id',
                'qwen3.5:2b',
                '--thinking-mode',
                'off',
                '--output',
                str(path),
            ]
            self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)
            original = path.read_bytes()
            self.assertEqual(json.loads(original)[0]['params']['think'], False)
            self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)
            self.assertEqual(path.read_bytes(), original)

    def test_cases_retain_all_fixture_ids_and_original_inputs(self):
        cases = load('evaluate').cases()
        self.assertEqual(len(cases), 12)
        by_id = {case: question for case, question, _ in cases}
        self.assertIn('<source id="1"', by_id['conflicting'])
        self.assertIn('<source id="2"', by_id['conflicting'])
        self.assertIn('<source id="4"', by_id['code-source'])
        self.assertEqual(by_id['concise'], 'In one sentence, what is a door schedule?')

    def test_prompt_pairs_keep_identical_provider_settings_and_question(self):
        evaluator = load('evaluate')
        for prefix in ('q3', 'q35'):
            mode = 'soft' if prefix == 'q3' else 'off'
            original, _ = evaluator.make_request(f'{prefix}-v01-{mode}', 'same question', 1)
            shorter, _ = evaluator.make_request(f'{prefix}-v02-{mode}', 'same question', 1)
            self.assertNotEqual(original['messages'][0], shorter['messages'][0])
            original['messages'].pop(0)
            shorter['messages'].pop(0)
            self.assertEqual(original, shorter)


if __name__ == '__main__':
    unittest.main()
