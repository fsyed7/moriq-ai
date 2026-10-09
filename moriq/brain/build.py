"""Build a native Open WebUI workspace-model import; no server changes or network I/O."""

import argparse
import json
import re
from pathlib import Path

RESOURCE_DIR = Path(__file__).resolve().parent


def build_model(base_model_id: str) -> dict:
    """Bind the versioned behavior to an operator-selected upstream model ID."""
    config = json.loads((RESOURCE_DIR / 'config.json').read_text(encoding='utf-8'))
    prompt = (RESOURCE_DIR / 'system.md').read_text(encoding='utf-8').strip()
    if not re.fullmatch(r'\S+', base_model_id):
        raise ValueError('Use an exact, non-empty base model ID without whitespace.')
    if base_model_id == config['id']:
        raise ValueError('The base model cannot be the MORIQ workspace model itself.')
    if not re.fullmatch(r'\d+\.\d+\.\d+', config['version']):
        raise ValueError('Brain version must be MAJOR.MINOR.PATCH.')
    if not prompt.startswith(f'# MORIQ Brain {config["version"]}\n'):
        raise ValueError('Prompt heading and configuration version must match.')
    return {
        'id': config['id'],
        'base_model_id': base_model_id,
        'name': config['name'],
        'params': {'system': prompt},
        'meta': {
            'description': config['description'],
            'moriq_brain_version': config['version'],
            'capabilities': {
                'citations': True,
                'web_search': False,
                'image_generation': False,
                'code_interpreter': False,
                'terminal': False,
                'memory': False,
                'builtin_tools': False,
            },
        },
        # No public grants. Reimports also reset sharing; reapply intended grants.
        'access_grants': [],
        'is_active': True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-model-id', required=True, help='Exact connected model ID shown by Open WebUI')
    parser.add_argument(
        '--output', type=Path, required=True, help='New JSON import file; existing files are not overwritten'
    )
    args = parser.parse_args()
    try:
        models = [build_model(args.base_model_id)]
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x', encoding='utf-8', newline='\n') as output:
            json.dump(models, output, ensure_ascii=False, indent=2)
            output.write('\n')
    except (ValueError, OSError) as error:
        parser.exit(1, f'{error}\n')


if __name__ == '__main__':
    main()
