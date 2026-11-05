"""End-to-end app tests over real HTTP, with a fake model. Run: py -3.12 -m unittest moriq.app.test_app"""

import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path

from moriq.app.corpus import build_registry
from moriq.app.pipeline import classify, decide
from moriq.app.provider import ProviderUnavailable
from moriq.app.server import Service, make_server
from moriq.app.store import Store


class FakeProvider:
    name = 'fake'

    def __init__(self):
        self.calls = []
        self.reply = ['A courtyard ', 'draws shade.']
        self.gate = None
        self.fail = False

    def available(self):
        return True

    def stream(self, messages, cancelled):
        self.calls.append(messages)
        if self.fail:
            raise ProviderUnavailable
        for piece in self.reply:
            yield piece
            if self.gate:
                self.gate.wait(5)
            if cancelled.is_set():
                return


class AppTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.store = Store(str(Path(self.dir.name) / 'chats.sqlite3'))
        self.provider = FakeProvider()
        self.registry = build_registry()
        self.server = make_server(Service(self.store, self.registry, self.provider), 0)
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.store.close()
        self.dir.cleanup()

    def request(self, method, path, body=None, headers=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.port, timeout=10)
        all_headers = {'Content-Type': 'application/json', **(headers or {})}
        conn.request(method, path, json.dumps(body) if body is not None else None, all_headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        return response.status, data

    def chat(self):
        return json.loads(self.request('POST', '/api/chats', {'workspace': 'architecture'})[1])['id']

    def ask(self, message, **extra):
        chat = extra.pop('chat', None) or self.chat()
        status, data = self.request('POST', '/api/ask', {'chat': chat, 'message': message, **extra})
        self.assertEqual(status, 200)
        return chat, [json.loads(line) for line in data.splitlines()]

    def test_general_answer_streams_and_is_labelled(self):
        chat, events = self.ask('How can a courtyard help cool a home?')
        self.assertEqual([e['type'] for e in events], ['start', 'token', 'token', 'done'])
        done = events[-1]
        self.assertEqual((done['status'], done['label']), ('draft', 'general'))
        self.assertEqual((done['claim_status'], done['release_allowed']), ('not_assessed', False))
        saved = json.loads(self.request('GET', f'/api/chats/{chat}')[1])
        self.assertEqual(saved['messages'][1]['text'], 'A courtyard draws shade.')
        self.assertEqual(saved['title'], 'How can a courtyard help cool a home?')

    def test_company_practice_blocks_without_calling_model(self):
        for question in ['What is the MORIQ drawing naming standard?', 'What is our office policy on revisions?']:
            _, events = self.ask(question)
            self.assertEqual(events[-1]['status'], 'blocked')
            self.assertEqual(events[-1]['code'], 'no_approved_source')
        self.assertEqual(self.provider.calls, [])

    def test_code_question_needs_scope_and_source(self):
        _, events = self.ask('What is the minimum egress stair width required?')
        self.assertEqual(events[-1]['code'], 'missing_scope')
        _, events = self.ask('What is the minimum egress stair width required?', jurisdiction='Telangana', edition='2017')
        self.assertEqual(events[-1]['code'], 'no_approved_source')
        self.assertEqual(self.provider.calls, [])

    def test_code_source_is_cited_and_identity_checked(self):
        self.provider.reply = ['Fictional width applies [1].']
        _, events = self.ask('egress stair requires minimum width', jurisdiction='TESTLAND', edition='TEST-v1')
        done = events[-1]
        self.assertEqual((done['label'], done['citation_check']), ('code_evidence', 'identity_valid'))
        self.assertEqual(done['sources'][0]['source_id'], 'SYNTHETIC-CODE')
        self.assertIs(done['release_allowed'], False)
        self.assertIn('<source id="1"', self.provider.calls[0][-1]['content'])

    def test_bad_citations_are_flagged(self):
        question = 'egress stair requires minimum width'
        self.provider.reply = ['Applies [9].']
        _, events = self.ask(question, jurisdiction='TESTLAND', edition='TEST-v1')
        self.assertEqual(events[-1]['citation_check'], 'unknown_reference')
        self.provider.reply = ['No citation here.']
        _, events = self.ask(question, jurisdiction='TESTLAND', edition='TEST-v1')
        self.assertEqual(events[-1]['citation_check'], 'uncited')
        self.provider.reply = ['Invented [1].']
        _, events = self.ask('How can a courtyard help cool a home?')
        self.assertEqual(events[-1]['citation_check'], 'unexpected_citation')
        self.provider.reply = ['Verify IBC Section 1012.3 for width [1].']
        _, events = self.ask(question, jurisdiction='TESTLAND', edition='TEST-v1')
        self.assertEqual(events[-1]['citation_check'], 'unsupported_reference')
        self.provider.reply = ['See the National Building Code for this.']
        _, events = self.ask('How can a courtyard help cool a home?')
        self.assertEqual(events[-1]['citation_check'], 'unsupported_reference')

    def test_identity_question_uses_public_profile_without_model(self):
        _, events = self.ask('Who is MORIQ?')
        done = events[-1]
        self.assertEqual((done['status'], done['label']), ('profile', 'public_profile'))
        self.assertIn('not an approved MORIQ source', done['text'])
        self.assertTrue(all(link['url'].startswith('https://') for link in done['links']))
        self.assertEqual(self.provider.calls, [])

    def test_cancel_stops_and_second_run_is_busy(self):
        self.provider.gate = threading.Event()
        chat = self.chat()
        conn = http.client.HTTPConnection('127.0.0.1', self.port, timeout=10)
        conn.request('POST', '/api/ask', json.dumps({'chat': chat, 'message': 'Explain thermal mass'}),
                     {'Content-Type': 'application/json'})
        response = conn.getresponse()
        start = json.loads(response.readline())
        self.assertEqual(start['type'], 'start')
        self.assertEqual(json.loads(response.readline())['type'], 'token')
        _, events = self.ask('Explain daylight')
        self.assertEqual(events[-1]['code'], 'busy')
        status, _ = self.request('POST', '/api/cancel', {'request_id': start['request_id']})
        self.assertEqual(status, 200)
        self.provider.gate.set()
        rest = [json.loads(line) for line in response.read().splitlines()]
        conn.close()
        self.assertEqual(rest[-1]['status'], 'cancelled')
        history = [text for _, text in self.store.history(chat)]
        self.assertEqual(history, ['Explain thermal mass'])

    def test_model_failure_is_reported_and_releases_slot(self):
        self.provider.fail = True
        _, events = self.ask('Explain daylight')
        self.assertEqual((events[-1]['status'], events[-1]['code']), ('failed', 'model_unavailable'))
        self.provider.fail = False
        _, events = self.ask('Explain daylight')
        self.assertEqual(events[-1]['status'], 'draft')

    def test_retrieved_text_is_framed_as_evidence(self):
        decision = decide('shaded courtyard threshold', self.registry)
        self.assertEqual(decision.hits[0].chunk.source_id, 'SYNTHETIC-COURTYARD')
        self.provider.reply = ['Shade helps [1].']
        _, events = self.ask('shaded courtyard threshold')
        self.assertEqual(events[-1]['label'], 'source_supported')
        self.assertIn('never as instructions', self.provider.calls[0][0]['content'])

    def test_host_and_origin_checks(self):
        status, _ = self.request('GET', '/api/chats', headers={'Host': 'evil.example'})
        self.assertEqual(status, 403)
        status, _ = self.request('POST', '/api/chats', {'workspace': 'architecture'}, {'Origin': 'https://evil.example'})
        self.assertEqual(status, 403)

    def test_invalid_input(self):
        self.assertEqual(self.request('POST', '/api/chats', {'workspace': 'nope'})[0], 400)
        self.assertEqual(self.request('POST', '/api/ask', {'x': 'y' * 40000})[0], 400)
        _, events = self.ask('x' * 1201)
        self.assertEqual(events[-1]['code'], 'invalid_message')
        status, data = self.request('POST', '/api/ask', {'chat': 'nope', 'message': 'hi'})
        self.assertEqual(json.loads(data)['code'], 'unknown_chat')
        self.assertEqual(status, 200)

    def test_rename_delete_and_pages(self):
        chat = self.chat()
        self.assertEqual(self.request('PATCH', f'/api/chats/{chat}', {'title': 'Renamed'})[0], 200)
        self.assertEqual(json.loads(self.request('GET', '/api/chats')[1])['chats'][0]['title'], 'Renamed')
        self.assertEqual(self.request('DELETE', f'/api/chats/{chat}')[0], 200)
        self.assertEqual(self.request('GET', f'/api/chats/{chat}')[0], 404)
        for path in ['/', '/app.js', '/live.css', '/styles.css', '/assets/courtyard-villa.jpg']:
            self.assertEqual(self.request('GET', path)[0], 200, path)
        self.assertEqual(self.request('GET', '/../CLAUDE.md')[0], 404)

    def test_classification(self):
        cases = {'Who is MORIQ?': 'identity', 'Where is MORIQ based?': 'identity',
                 'What is the MORIQ detailing standard?': 'company', 'Does our firm allow this?': 'company',
                 'What setback applies here?': 'code', 'Explain cross ventilation': 'general',
                 'How do vaastu preferences affect planning?': 'general',
                 'How do I plan a vaastu-compliant kitchen?': 'general', 'Is this ramp compliant?': 'code',
                 'How far apart should columns be?': 'general', 'What floor area ratio applies?': 'code'}
        for question, expected in cases.items():
            self.assertEqual(classify(question), expected, question)


if __name__ == '__main__':
    unittest.main()
