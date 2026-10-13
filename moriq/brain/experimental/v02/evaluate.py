"""Sequential local-only experiments. Never imports models into Open WebUI."""

import argparse
import datetime as dt
import hashlib
import json
import re
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
BRAIN = HERE.parents[1]
PROFILES = {
    'q3-v01-soft': ('qwen3:4b', 'v01', 'soft'),
    'q3-v02-soft': ('qwen3:4b', 'v02', 'soft'),
    'q35-v01-off': ('qwen3.5:2b', 'v01', 'off'),
    'q35-v02-off': ('qwen3.5:2b', 'v02', 'off'),
    'q3-v02-default': ('qwen3:4b', 'v02', 'default'),
}


def cases():
    matrix = (BRAIN / 'evaluation.md').read_text(encoding='utf-8')
    fixtures = dict(zip('ABCD', re.findall(r'```xml\n(.*?)\n```', matrix, re.S)))
    result = []
    for line in matrix.splitlines():
        if not line.startswith('| ') or line.startswith(('| ID ', '| ---')):
            continue
        case, question, rubric = [value.strip() for value in line.strip('|').split('|')]
        fixture = re.search(r'Use fixture ([A-D]) below', question)
        if fixture:
            question += '\n\n' + fixtures[fixture[1]]
        result.append((case, question, rubric))
    if len(result) != 12:
        raise ValueError('Expected the unchanged twelve-case matrix')
    return result


def request(body, endpoint='chat', timeout=90):
    return urllib.request.urlopen(
        urllib.request.Request(
            'http://127.0.0.1:11434/api/' + endpoint,
            json.dumps(body).encode(),
            {'Content-Type': 'application/json'},
        ),
        timeout=timeout,
    )


def make_request(profile, question, repetition):
    model, version, thinking = PROFILES[profile]
    path = BRAIN / 'system.md' if version == 'v01' else HERE / 'system.md'
    system = path.read_text(encoding='utf-8').strip()
    canonical_hash = hashlib.sha256(system.encode()).hexdigest()
    if thinking == 'soft':
        system += '\n\n/no_think'
    body = {
        'model': model,
        'messages': [{'role': 'system', 'content': system}, {'role': 'user', 'content': question}],
        'stream': True,
        'keep_alive': '5m',
        'options': {
            'num_ctx': 4096,
            'num_predict': 1500,
            'temperature': 0.2,
            'top_p': 0.95,
            'top_k': 20,
            'repeat_penalty': 1,
            'presence_penalty': 0,
            'seed': 100 + repetition,
        },
    }
    if thinking == 'off':
        body['think'] = False
    return body, canonical_hash


def run(profile, case, question, rubric, repetition):
    body, canonical_hash = make_request(profile, question, repetition)
    record = {
        'profile': profile,
        'case': case,
        'repetition': repetition,
        'time_utc': dt.datetime.now(dt.UTC).isoformat(),
        'prompt_sha256': canonical_hash,
        'request': body,
        'rubric': rubric,
        'answer': '',
        'thinking': '',
        'tool_calls': [],
        'transport_complete': False,
        'assessment': 'NOT REVIEWED',
    }
    started = time.monotonic()
    previous = started
    try:
        with request(body) as response:
            for raw in response:
                now = time.monotonic()
                if now - previous > 120:
                    record['timing_warning'] = 'Long delivery gap; exclude latency from comparison.'
                previous = now
                if now - started > 360:
                    raise TimeoutError('Active deadline exceeded; stop batch and inspect provider before resuming.')
                chunk = json.loads(raw)
                if 'error' in chunk:
                    raise RuntimeError(chunk['error'])
                message = chunk.get('message', {})
                record['answer'] += message.get('content', '')
                record['thinking'] += message.get('thinking', '')
                record['tool_calls'].extend(message.get('tool_calls', []))
                if message.get('content') and 'first_answer_seconds' not in record:
                    record['first_answer_seconds'] = round(now - started, 3)
                if chunk.get('done'):
                    record['transport_complete'] = True
                    record['metrics'] = {k: v for k, v in chunk.items() if k != 'message'}
                    break
    except Exception as exc:
        record['error'] = str(exc)
    record['wall_seconds'] = round(time.monotonic() - started, 3)
    if record['wall_seconds'] > 360:
        record['timing_warning'] = 'Deadline/suspension exceeded; exclude latency from comparison.'
    record['delivery_complete'] = bool(
        record['transport_complete']
        and record.get('metrics', {}).get('done_reason') == 'stop'
        and record['answer'].strip()
        and not record.get('error')
    )
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profiles', nargs='+', choices=PROFILES, required=True)
    parser.add_argument('--cases', nargs='+')
    parser.add_argument('--repetitions', type=int, default=1)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not 1 <= args.repetitions <= 3:
        parser.error('Use one to three repetitions')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    existing = []
    if args.output.exists():
        existing = [json.loads(line) for line in args.output.read_text(encoding='utf-8').splitlines()]
    done = {(r['profile'], r['case'], r['repetition']) for r in existing}
    for profile in args.profiles:
        for repetition in range(1, args.repetitions + 1):
            for case, question, rubric in cases():
                if args.cases and case not in args.cases:
                    continue
                if (profile, case, repetition) in done:
                    continue
                print(f'START {profile} {case} r{repetition}', flush=True)
                record = run(profile, case, question, rubric, repetition)
                with args.output.open('a', encoding='utf-8', newline='\n') as output:
                    output.write(json.dumps(record, ensure_ascii=False) + '\n')
                print(
                    json.dumps({k: v for k, v in record.items() if k not in ('request', 'thinking', 'rubric')}),
                    flush=True,
                )
                if record.get('error'):
                    raise SystemExit('Stopped after error; do not queue requests behind a possibly active generation.')


if __name__ == '__main__':
    main()
