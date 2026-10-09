"""Configuration/CLI and isolated pinned-upstream prompt composition tests.

These do not score LLM answers or run the full Open WebUI application.
"""

import ast
import asyncio
import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

try:
    import pydantic
except ImportError:
    pydantic = None

BRAIN = Path(__file__).resolve().parents[1]
ROOT = BRAIN.parents[1]
spec = importlib.util.spec_from_file_location('brain_build', BRAIN / 'build.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def load_upstream_functions(relative_path, names, namespace):
    """Execute actual selected upstream helpers without booting DB/provider imports."""
    path = ROOT / relative_path
    tree = ast.parse(path.read_text(encoding='utf-8'))
    nodes = [
        node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in names
    ]
    if {node.name for node in nodes} != set(names):
        raise AssertionError(f'Pinned upstream helper contract changed: {path}')
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), namespace)


class BuildTests(unittest.TestCase):
    def test_provider_selection_does_not_change_behavior(self):
        first = builder.build_model('provider-a/architecture-model')
        second = builder.build_model('local-model:latest')
        self.assertNotEqual(first.pop('base_model_id'), second.pop('base_model_id'))
        self.assertEqual(first, second)
        self.assertEqual(first['access_grants'], [])
        self.assertEqual(set(first['params']), {'system'})
        self.assertNotIn('knowledge', first['meta'])
        self.assertNotIn('filterIds', first['meta'])
        self.assertTrue(first['meta']['capabilities']['citations'])
        self.assertFalse(any(value for key, value in first['meta']['capabilities'].items() if key != 'citations'))
        self.assertEqual(first['params']['system'], (BRAIN / 'system.md').read_text(encoding='utf-8').strip())

    def test_invalid_or_self_referencing_base_model_is_rejected(self):
        for value in ('', ' ', ' model', 'model\n', 'two models', 'moriq-ai'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                builder.build_model(value)

    def test_version_mismatch_is_rejected(self):
        original = builder.RESOURCE_DIR
        with tempfile.TemporaryDirectory() as directory:
            try:
                builder.RESOURCE_DIR = Path(directory)
                (Path(directory) / 'config.json').write_text((BRAIN / 'config.json').read_text(encoding='utf-8'))
                (Path(directory) / 'system.md').write_text('# MORIQ Brain 99.0.0\nWrong version')
                with self.assertRaisesRegex(ValueError, 'version must match'):
                    builder.build_model('test-base')
            finally:
                builder.RESOURCE_DIR = original

    def test_cli_exports_import_array_from_another_directory_and_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'nested' / 'model.json'
            command = [sys.executable, str(BRAIN / 'build.py'), '--base-model-id', 'test-base', '--output', str(output)]
            result = subprocess.run(command, cwd=directory, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(output.read_text(encoding='utf-8')), [builder.build_model('test-base')])
            before = output.read_bytes()
            repeated = subprocess.run(command, cwd=directory, capture_output=True, text=True)
            self.assertNotEqual(repeated.returncode, 0)
            self.assertEqual(output.read_bytes(), before)

    def test_invalid_cli_does_not_create_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'model.json'
            result = subprocess.run(
                [sys.executable, str(BRAIN / 'build.py'), '--base-model-id', 'moriq-ai', '--output', str(output)],
                capture_output=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output.exists())


class UpstreamCompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Variable/template resolution is outside this test; the prompt has no variables.
        async def resolve_system_prompt(system, metadata=None, user=None):
            return system

        cls.namespace = {'Optional': __import__('typing').Optional, 'resolve_system_prompt': resolve_system_prompt}
        load_upstream_functions(
            'backend/open_webui/utils/misc.py',
            {'update_message_content', 'add_or_update_system_message', 'replace_system_message_content'},
            cls.namespace,
        )
        load_upstream_functions('backend/open_webui/utils/payload.py', {'apply_system_prompt_to_body'}, cls.namespace)

    def test_prompt_preserves_existing_context_citations_and_non_system_payload(self):
        prompt = builder.build_model('test-base')['params']['system']
        context = '<source id="7" name="Synthetic reference">Example evidence only.</source>'
        for content in (context, [{'type': 'text', 'text': context}]):
            for context_role in ('system', 'user'):
                with self.subTest(content=content, context_role=context_role):
                    body = {
                        'model': 'test-base',
                        'messages': [{'role': context_role, 'content': copy.deepcopy(content)}],
                        'metadata': {'sources': [{'id': '7', 'name': 'Synthetic reference'}]},
                        'stream': True,
                    }
                    original = copy.deepcopy(body)
                    result = asyncio.run(self.namespace['apply_system_prompt_to_body'](prompt, body))
                    self.assertEqual(result['metadata'], original['metadata'])
                    self.assertEqual(result['model'], original['model'])
                    self.assertTrue(result['stream'])
                    self.assertEqual(result['messages'][0]['role'], 'system')
                    serialized = json.dumps(result['messages'], ensure_ascii=False)
                    self.assertIn('MORIQ Brain 0.1.0', serialized)
                    if context_role == 'user':
                        self.assertEqual(result['messages'][1], original['messages'][0])
                    else:
                        actual = result['messages'][0]['content']
                        text = actual[0]['text'] if isinstance(actual, list) else actual
                        self.assertEqual(text, prompt + '\n' + context)

    def test_empty_chat_receives_system_prompt(self):
        prompt = builder.build_model('test-base')['params']['system']
        result = asyncio.run(self.namespace['apply_system_prompt_to_body'](prompt, {'messages': []}))
        self.assertEqual(result['messages'], [{'role': 'system', 'content': prompt}])


@unittest.skipUnless(pydantic and pydantic.__version__.startswith('2.'), 'Requires Pydantic 2 for upstream schema')
class UpstreamSchemaTests(unittest.TestCase):
    def test_generated_model_validates_without_dropping_prompt_or_access_settings(self):
        path = ROOT / 'backend/open_webui/models/models.py'
        names = {'ModelParams', 'ModelMeta', 'ModelForm'}
        nodes = [
            node
            for node in ast.parse(path.read_text(encoding='utf-8')).body
            if isinstance(node, ast.ClassDef) and node.name in names
        ]
        self.assertEqual({node.name for node in nodes}, names)
        namespace = {'__name__': __name__, 'Any': Any}
        for name in ('BaseModel', 'ConfigDict', 'Field', 'ValidationInfo', 'field_validator', 'model_validator'):
            namespace[name] = getattr(pydantic, name)
        # Actual upstream schemas; no database imports. The generated model does
        # not supply images, tags, or knowledge, so their validators are not exercised.
        exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), namespace)
        model = builder.build_model('test-base')
        validated = namespace['ModelForm'].model_validate(model).model_dump(exclude_unset=True)
        self.assertEqual(validated, model)


if __name__ == '__main__':
    unittest.main()
