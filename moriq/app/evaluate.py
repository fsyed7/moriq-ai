"""Live spot check against the configured model. Run: py -3.12 -m moriq.app.evaluate [output.json]

These checks test routing, scope and references. They do not grade architectural correctness,
so a person still needs to read the saved answers.
"""

import json
import sys
import threading
import time

from moriq.app.corpus import build_registry
from moriq.app.knowledge import Knowledge
from moriq.app.pipeline import OUT_OF_SCOPE_MARK, build_messages, decide, finish
from moriq.app.provider import ProviderUnavailable, make_provider

BAD_CHECKS = {'unsupported_reference', 'unsupported_limit', 'unknown_reference', 'unexpected_citation', 'stale_or_invalid'}
IN_SCOPE = 'in_scope'
CASES = [
    ('How can a courtyard help cool a home in a hot climate?', IN_SCOPE),
    ('How does vaastu affect kitchen placement on a narrow linear plot?', IN_SCOPE),
    ('How do beams and columns carry load to the foundation?', IN_SCOPE),
    ('What should I check where timber decking meets pebble paving?', IN_SCOPE),
    ('How should a parapet be detailed against rainwater?', IN_SCOPE),
    ('What is a setback?', IN_SCOPE),
    ('What projects has MORIQ designed in Bahrain?', IN_SCOPE),
    ('How do I get a building permit in Bahrain?', IN_SCOPE),
    ('What should an architect appointment letter include?', IN_SCOPE),
    ('Which marble care issues matter in a kitchen?', IN_SCOPE),
    ('What is the MORIQ leave policy?', 'no_approved_source'),
    ('What is the capital of France?', OUT_OF_SCOPE_MARK),
    ('Who won the last election?', OUT_OF_SCOPE_MARK),
    ('Write a Python function that sorts a list.', OUT_OF_SCOPE_MARK),
    ('What is the best way to lose weight?', OUT_OF_SCOPE_MARK),
]


def run_case(question, expected, registry, knowledge, provider):
    decision = decide(question, registry, knowledge)
    started = time.monotonic()
    row = {'question': question, 'expected': expected, 'category': decision.category}
    if decision.action != 'answer':
        row.update(outcome=OUT_OF_SCOPE_MARK if decision.code == 'out_of_scope' else decision.code, seconds=0.0, answer=decision.message)
    else:
        try:
            answer = ''.join(provider.stream(build_messages(decision, question), threading.Event()))
        except ProviderUnavailable:
            answer = ''
        row.update(seconds=round(time.monotonic() - started, 1), answer=answer)
        if answer.strip().startswith(OUT_OF_SCOPE_MARK):
            row['outcome'] = OUT_OF_SCOPE_MARK
        elif not answer.strip():
            row['outcome'] = 'no_answer'
        else:
            meta = finish(decision, answer, registry)
            row.update(outcome=IN_SCOPE, label=meta['label'], citation_check=meta['citation_check'])
    row['passed'] = row['outcome'] == expected and row.get('citation_check') not in BAD_CHECKS
    return row


def main():
    registry, knowledge, provider = build_registry(), Knowledge(), make_provider()
    results = []
    for question, expected in CASES:
        row = run_case(question, expected, registry, knowledge, provider)
        results.append(row)
        print(f"{'PASS' if row['passed'] else 'FAIL'} {row['seconds']:>6}s {row['outcome']:<14} "
              f"{row.get('label', '-'):<14} {row.get('citation_check', '-'):<22} {question}", flush=True)
    passed = sum(row['passed'] for row in results)
    print(f'{passed}/{len(results)} passed on {provider.name}', flush=True)
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'w', encoding='utf-8') as handle:
            json.dump({'model': provider.name, 'passed': passed, 'total': len(results), 'results': results}, handle, indent=1)


if __name__ == '__main__':
    main()
