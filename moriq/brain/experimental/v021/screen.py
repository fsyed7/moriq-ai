"""Run a frozen, approved local screening manifest; never pull or import models."""

import argparse
import ctypes
import datetime as dt
import hashlib
import json
import threading
import time
import urllib.request
from pathlib import Path

MODEL = 'qwen3:4b-instruct-2507-q4_K_M'


class Memory(ctypes.Structure):
    _fields_ = [('length', ctypes.c_ulong), ('load', ctypes.c_ulong)] + [
        (name, ctypes.c_ulonglong)
        for name in (
            'total',
            'available',
            'page_total',
            'page_available',
            'virtual_total',
            'virtual_available',
            'extended',
        )
    ]


def available_memory():
    memory = Memory()
    memory.length = ctypes.sizeof(memory)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)):
        raise ctypes.WinError()
    return memory.available / 2**30


def api(endpoint, body=None):
    request = urllib.request.Request(
        'http://127.0.0.1:11434/api/' + endpoint,
        None if body is None else json.dumps(body).encode(),
        {'Content-Type': 'application/json'},
    )
    return urllib.request.urlopen(request, timeout=90 if endpoint == 'chat' else 10)


def loaded_models():
    with api('ps') as response:
        return json.load(response)['models']


def check_loaded(models):
    if len(models) > 1 or any(m['name'] != MODEL or m.get('size_vram') != 0 for m in models):
        raise RuntimeError('Competing model or non-CPU runner observed; stop screening.')


def validate_plan(plan):
    if len(plan) != 12:
        raise ValueError('Only the approved twelve-request screen is allowed.')
    for row in plan:
        body = row['request']
        if (
            body['model'] != MODEL
            or body['keep_alive'] != 0
            or body['options']['num_gpu'] != 0
            or body.get('tools')
            or len(body['messages']) != 2
        ):
            raise ValueError('Unexpected model, persistence, tools or context.')
    for index in range(0, len(plan), 2):
        pair = plan[index : index + 2]
        if pair[0]['case'] != pair[1]['case'] or {r['version'] for r in pair} != {'v01', 'v021'}:
            raise ValueError('Unpaired prompts.')
        bodies = [json.loads(json.dumps(r['request'])) for r in pair]
        for body in bodies:
            body['messages'].pop(0)
        if bodies[0] != bodies[1]:
            raise ValueError('Prompt comparison has unequal settings or questions.')


def receive(row, record, started, problems):
    with api('chat', row['request']) as response:
        for raw in response:
            elapsed = time.monotonic() - started
            if problems or elapsed > 360:
                raise RuntimeError('; '.join(problems) or '360-second deadline exceeded.')
            chunk = json.loads(raw)
            if chunk.get('error'):
                raise RuntimeError(chunk['error'])
            message = chunk.get('message', {})
            if message.get('content') and 'first_answer_seconds' not in record:
                record['first_answer_seconds'] = round(elapsed, 3)
            record['answer'] += message.get('content', '')
            record['thinking'] += message.get('thinking', '')
            record['tool_calls'].extend(message.get('tool_calls', []))
            if chunk.get('done'):
                record['transport_complete'] = True
                record['metrics'] = {k: v for k, v in chunk.items() if k != 'message'}
                break


def confirm_unloaded(record):
    for _ in range(15):
        if not loaded_models():
            record['unloaded_after_request'] = True
            break
        time.sleep(1)
    if not record.get('unloaded_after_request'):
        record['error'] = record.get('error', '') + ' Model did not unload; inspect before continuing.'


def run(row):
    if loaded_models():
        raise RuntimeError('Model already loaded: inspect for competing work; no automatic unload.')
    before = available_memory()
    if before < 5:
        raise RuntimeError(f'Only {before:.2f} GiB RAM available; require 5 before loading.')
    record = dict(row)
    record.update(
        status='EXECUTED',
        utc=dt.datetime.now(dt.UTC).isoformat(),
        answer='',
        thinking='',
        tool_calls=[],
        samples=[],
        transport_complete=False,
    )
    started = time.monotonic()
    finished = threading.Event()
    problems = []

    def monitor():
        while not finished.is_set():
            try:
                memory = available_memory()
                models = loaded_models()
                record['samples'].append(
                    {
                        'seconds': round(time.monotonic() - started, 3),
                        'available_ram_gib': round(memory, 3),
                        'models': models,
                    }
                )
                check_loaded(models)
                if memory < 1.5:
                    raise RuntimeError('Available RAM below 1.5 GiB.')
            except Exception as exc:
                problems.append(str(exc))
                return
            finished.wait(2)

    watcher = threading.Thread(target=monitor, daemon=True)
    watcher.start()
    try:
        receive(row, record, started, problems)
    except Exception as exc:
        record['error'] = str(exc)
    finally:
        record['wall_seconds'] = round(time.monotonic() - started, 3)
        finished.set()
        watcher.join(timeout=35)
    if problems:
        record['error'] = '; '.join(problems)
    record['cpu_observed'] = any(s['models'] for s in record['samples']) and not problems
    record['delivery_transport'] = bool(
        record['transport_complete']
        and record['answer'].strip()
        and record.get('metrics', {}).get('done_reason') == 'stop'
        and not record.get('error')
    )
    record['semantic_review'] = 'NOT REVIEWED'
    confirm_unloaded(record)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    plan_bytes = args.plan.read_bytes()
    plan = json.loads(plan_bytes)
    validate_plan(plan)
    plan_hash = hashlib.sha256(plan_bytes).hexdigest()
    prior = (
        [json.loads(line) for line in args.output.read_text(encoding='utf-8').splitlines()]
        if args.output.exists()
        else []
    )
    if any(r['plan_sha256'] != plan_hash or r.get('error') for r in prior):
        raise RuntimeError('Changed plan or recorded error; preserve results and review before resuming.')
    done = {(r['case'], r['version']) for r in prior}
    for row in plan:
        if (row['case'], row['version']) in done:
            continue
        print(f'START {row["case"]} {row["version"]}', flush=True)
        record = run(row)
        record['plan_sha256'] = plan_hash
        with args.output.open('a', encoding='utf-8', newline='\n') as output:
            output.write(json.dumps(record, ensure_ascii=False) + '\n')
        print(
            json.dumps(
                {
                    k: v
                    for k, v in record.items()
                    if k
                    in (
                        'case',
                        'version',
                        'wall_seconds',
                        'first_answer_seconds',
                        'error',
                        'delivery_transport',
                        'cpu_observed',
                        'unloaded_after_request',
                    )
                }
            ),
            flush=True,
        )
        if record.get('error'):
            raise SystemExit('Stopped after error. Client cancellation does not prove server idle.')


if __name__ == '__main__':
    main()
