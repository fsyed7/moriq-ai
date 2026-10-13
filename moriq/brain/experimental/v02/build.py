"""Create a disabled, private V0.2 import artifact; never modify V0.1 or a server."""

import argparse
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent


def build_model(base_model_id, thinking_mode):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/-]*', base_model_id):
        raise ValueError('Use an exact model identifier without whitespace')
    if base_model_id.startswith('moriq-ai'):
        raise ValueError('Use a provider model, not a MORIQ workspace model')
    if thinking_mode not in ('default', 'soft', 'off'):
        raise ValueError('Unknown thinking mode')
    config = json.loads((HERE / 'config.json').read_text(encoding='utf-8'))
    system = (HERE / 'system.md').read_text(encoding='utf-8').strip()
    if not system.startswith('# MORIQ Brain ' + config['version'] + '\n'):
        raise ValueError('Prompt/config version mismatch')
    if thinking_mode == 'soft':
        system += '\n\n/no_think'
    suffix = re.sub(r'[^a-z0-9-]', '-', base_model_id.lower())
    params = {
        'system': system,
        'temperature': 0.2,
        'top_p': 0.95,
        'top_k': 20,
        'repeat_penalty': 1,
        'presence_penalty': 0,
        'num_ctx': 4096,
        'max_tokens': 1500,
        'keep_alive': '5m',
    }
    if thinking_mode == 'off':
        params['think'] = False
    return {
        'id': config['id'] + '-' + suffix + '-' + thinking_mode,
        'name': config['name'] + ' / ' + base_model_id + ' / ' + thinking_mode,
        'base_model_id': base_model_id,
        'params': params,
        'meta': {
            'description': 'Unvalidated experiment. Not a replacement for MORIQ AI V0.1.',
            'moriq_brain_version': config['version'],
            'capabilities': config['capabilities'],
        },
        'access_grants': [],
        'is_active': False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-model-id', required=True)
    parser.add_argument('--thinking-mode', choices=('default', 'soft', 'off'), required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        model = build_model(args.base_model_id, args.thinking_mode)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x', encoding='utf-8', newline='\n') as output:
            json.dump([model], output, ensure_ascii=False, indent=2)
            output.write('\n')
    except (ValueError, OSError) as error:
        parser.exit(1, f'{error}\n')


if __name__ == '__main__':
    main()
