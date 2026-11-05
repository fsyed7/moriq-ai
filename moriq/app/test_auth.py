"""Accounts over real HTTP. Run: py -3.12 -B -m unittest moriq.app.test_auth"""

import http.client
import json
import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path

from moriq.app.auth import FAILURE_WINDOW, MAX_FAILURES, AccountError, Accounts, check_password, hash_password, verify_password
from moriq.app.corpus import build_registry
from moriq.app.knowledge import Knowledge
from moriq.app.server import Config, Service, make_server
from moriq.app.store import Store
from moriq.app.test_app import FakeProvider

GOOD = 'a long test passphrase'


class Browser:
    """Keeps a session cookie, as a browser would."""

    def __init__(self, test, host=None, origin=None):
        self.test, self.cookie, self.host, self.origin = test, None, host, origin
        self.set_cookie = None

    def call(self, method, path, body=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.test.port, timeout=15)
        headers = {'Content-Type': 'application/json'}
        if self.cookie:
            headers['Cookie'] = self.cookie
        if self.host:
            headers['Host'] = self.host
        if self.origin:
            headers['Origin'] = self.origin
        conn.request(method, path, json.dumps(body) if body is not None else None, headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()
        cookie = response.getheader('Set-Cookie')
        if cookie:
            self.set_cookie = cookie
            value = cookie.split(';')[0]
            self.cookie = None if value.endswith('=') else value
        try:
            return response.status, json.loads(data)
        except ValueError:
            return response.status, data


class AuthCase(unittest.TestCase):
    config = None

    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = str(Path(self.dir.name) / 'chats.sqlite3')
        self.store = Store(self.path)
        self.provider = FakeProvider()
        self.service = Service(self.store, build_registry(), self.provider, Knowledge())
        self.service.queue_seconds = 0
        self.accounts = self.service.accounts
        self.server = make_server(self.service, 0, self.config)
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.store.close()
        self.dir.cleanup()

    def admin(self):
        browser = Browser(self)
        status, _ = browser.call('POST', '/api/setup', {'username': 'owner', 'name': 'Owner', 'password': GOOD})
        self.assertEqual(status, 201)
        return browser

    def member(self, admin, username='nadia'):
        status, reply = admin.call('POST', '/api/users', {'username': username, 'name': username.title()})
        self.assertEqual(status, 201)
        browser = Browser(self)
        self.assertEqual(browser.call('POST', '/api/login', {'username': username, 'password': reply['temporary_password']})[0], 200)
        self.assertEqual(browser.call('POST', '/api/password', {'current': reply['temporary_password'], 'new': GOOD + ' two'})[0], 200)
        return browser


class AccountsTest(AuthCase):
    def test_everything_private_needs_sign_in(self):
        browser = Browser(self)
        for method, path, body in [('GET', '/api/status', None), ('GET', '/api/chats', None), ('GET', '/api/users', None),
                                   ('POST', '/api/chats', {'workspace': 'architecture'}), ('POST', '/api/ask', {'chat': 'x', 'message': 'hi'}),
                                   ('POST', '/api/cancel', {'request_id': 'x'}), ('POST', '/api/password', {'current': 'x', 'new': 'y'}),
                                   ('PATCH', '/api/chats/' + 'a' * 32, {'title': 'x'}), ('DELETE', '/api/chats/' + 'a' * 32, None),
                                   ('GET', '/api/chats/' + 'a' * 32, None)]:
            self.assertEqual(browser.call(method, path, body)[0], 401, path)
        self.assertEqual(browser.call('GET', '/')[0], 200)
        self.assertEqual(browser.call('GET', '/api/health')[1], {'app': 'moriq-ai'})

    def test_first_run_makes_one_admin_only(self):
        browser = Browser(self)
        state = browser.call('GET', '/api/session')[1]
        self.assertTrue(state['needs_setup'])
        self.assertFalse(state['setup_code_required'])
        self.assertEqual(browser.call('POST', '/api/setup', {'username': 'owner', 'name': 'Owner', 'password': 'short'})[1]['code'], 'weak_password')
        self.admin()
        self.assertEqual(Browser(self).call('POST', '/api/setup', {'username': 'thief', 'name': 'T', 'password': GOOD})[0], 409)
        self.assertFalse(Browser(self).call('GET', '/api/session')[1]['needs_setup'])

    def test_cookie_is_protected_and_token_is_not_stored(self):
        browser = self.admin()
        for attribute in ('HttpOnly', 'SameSite=Strict', 'Path=/'):
            self.assertIn(attribute, browser.set_cookie)
        token = browser.cookie.split('=', 1)[1]
        db = sqlite3.connect(self.path)
        dump = '\n'.join(db.iterdump())
        db.close()
        self.assertNotIn(token, dump)
        self.assertNotIn(GOOD, dump)
        self.assertIn('scrypt$', dump)

    def test_sign_out_ends_the_session_on_the_server(self):
        browser = self.admin()
        stolen = browser.cookie
        self.assertEqual(browser.call('POST', '/api/logout', {})[0], 200)
        self.assertIsNone(browser.cookie)
        copy = Browser(self)
        copy.cookie = stolen
        self.assertEqual(copy.call('GET', '/api/chats')[0], 401)

    def test_people_cannot_reach_each_others_chats(self):
        admin = self.admin()
        nadia = self.member(admin)
        chat = admin.call('POST', '/api/chats', {'workspace': 'architecture'})[1]['id']
        admin.call('POST', '/api/ask', {'chat': chat, 'message': 'How do I detail a roof?'})
        self.assertEqual(nadia.call('GET', '/api/chats')[1]['chats'], [])
        self.assertEqual(nadia.call('GET', f'/api/chats/{chat}')[0], 404)
        self.assertEqual(nadia.call('PATCH', f'/api/chats/{chat}', {'title': 'stolen'})[0], 404)
        self.assertEqual(nadia.call('DELETE', f'/api/chats/{chat}')[0], 404)
        _, reply = nadia.call('POST', '/api/ask', {'chat': chat, 'message': 'How do I detail a wall?'})
        self.assertEqual(reply['code'], 'unknown_chat')
        saved = admin.call('GET', f'/api/chats/{chat}')[1]
        self.assertEqual(saved['title'], 'How do I detail a roof?')
        self.assertEqual(len(saved['messages']), 2)

    def test_people_cannot_stop_each_others_answers(self):
        admin = self.admin()
        nadia = self.member(admin)
        self.provider.gate = threading.Event()
        self.provider.reply = ['Thermal mass ', 'stores heat.']
        chat = admin.call('POST', '/api/chats', {'workspace': 'architecture'})[1]['id']
        conn = http.client.HTTPConnection('127.0.0.1', self.port, timeout=15)
        conn.request('POST', '/api/ask', json.dumps({'chat': chat, 'message': 'Explain thermal mass'}),
                     {'Content-Type': 'application/json', 'Cookie': admin.cookie})
        response = conn.getresponse()
        request_id = json.loads(response.readline())['request_id']
        self.assertEqual(nadia.call('POST', '/api/cancel', {'request_id': request_id})[0], 404)
        self.assertEqual(admin.call('POST', '/api/cancel', {'request_id': request_id})[0], 200)
        self.provider.gate.set()
        response.read()
        conn.close()

    def test_second_person_queues_and_gets_an_answer(self):
        admin = self.admin()
        nadia = self.member(admin)
        self.service.queue_seconds = 10
        self.provider.gate = threading.Event()
        self.provider.reply = ['First ', 'answer.']
        first = admin.call('POST', '/api/chats', {'workspace': 'architecture'})[1]['id']
        second = nadia.call('POST', '/api/chats', {'workspace': 'interiors'})[1]['id']
        conn = http.client.HTTPConnection('127.0.0.1', self.port, timeout=15)
        conn.request('POST', '/api/ask', json.dumps({'chat': first, 'message': 'Explain thermal mass'}),
                     {'Content-Type': 'application/json', 'Cookie': admin.cookie})
        response = conn.getresponse()
        response.readline()
        result = {}

        def ask():
            result['reply'] = nadia.call('POST', '/api/ask', {'chat': second, 'message': 'Explain daylight in rooms'})[1]
        worker = threading.Thread(target=ask)
        worker.start()
        self.provider.gate.set()
        response.read()
        conn.close()
        worker.join(10)
        events = [json.loads(line) for line in result['reply'].splitlines()]
        self.assertEqual(events[-1]['status'], 'draft')

    def test_only_admins_manage_people(self):
        admin = self.admin()
        nadia = self.member(admin)
        owner = next(u for u in self.accounts.list_users() if u['username'] == 'owner')
        self.assertEqual(nadia.call('GET', '/api/users')[0], 403)
        self.assertEqual(nadia.call('POST', '/api/users', {'username': 'evil', 'name': 'Evil', 'role': 'admin'})[0], 403)
        self.assertEqual(nadia.call('POST', f"/api/users/{owner['id']}/reset", {})[0], 403)
        self.assertEqual(nadia.call('POST', f"/api/users/{owner['id']}/active", {'active': False})[0], 403)
        listing = admin.call('GET', '/api/users')[1]['users']
        self.assertEqual({u['username'] for u in listing}, {'owner', 'nadia'})
        self.assertNotIn('password', json.dumps(listing))

    def test_new_person_must_change_temporary_password_first(self):
        admin = self.admin()
        _, reply = admin.call('POST', '/api/users', {'username': 'omar', 'name': 'Omar'})
        browser = Browser(self)
        state = browser.call('POST', '/api/login', {'username': 'omar', 'password': reply['temporary_password']})[1]
        self.assertTrue(state['user']['must_change'])
        self.assertEqual(browser.call('GET', '/api/chats')[1]['code'], 'password_change_required')
        self.assertEqual(browser.call('POST', '/api/password', {'current': 'wrong password', 'new': GOOD})[1]['code'], 'wrong_password')
        self.assertEqual(browser.call('POST', '/api/password', {'current': reply['temporary_password'], 'new': 'short'})[1]['code'], 'weak_password')
        self.assertEqual(browser.call('POST', '/api/password', {'current': reply['temporary_password'], 'new': GOOD})[0], 200)
        self.assertEqual(browser.call('GET', '/api/chats')[0], 200)

    def test_disabling_someone_signs_them_out_and_blocks_sign_in(self):
        admin = self.admin()
        nadia = self.member(admin)
        user = next(u for u in self.accounts.list_users() if u['username'] == 'nadia')
        self.assertEqual(admin.call('POST', f"/api/users/{user['id']}/active", {'active': False})[0], 200)
        self.assertEqual(nadia.call('GET', '/api/chats')[0], 401)
        self.assertEqual(Browser(self).call('POST', '/api/login', {'username': 'nadia', 'password': GOOD + ' two'})[0], 401)
        self.assertEqual(admin.call('POST', f"/api/users/{user['id']}/active", {'active': True})[0], 200)
        self.assertEqual(Browser(self).call('POST', '/api/login', {'username': 'nadia', 'password': GOOD + ' two'})[0], 200)

    def test_admin_cannot_lock_everyone_out(self):
        admin = self.admin()
        owner = next(u for u in self.accounts.list_users() if u['username'] == 'owner')
        self.assertEqual(admin.call('POST', f"/api/users/{owner['id']}/active", {'active': False})[1]['code'], 'cannot_disable_self')

    def test_password_reset_invalidates_old_password_and_sessions(self):
        admin = self.admin()
        nadia = self.member(admin)
        user = next(u for u in self.accounts.list_users() if u['username'] == 'nadia')
        temporary = admin.call('POST', f"/api/users/{user['id']}/reset", {})[1]['temporary_password']
        self.assertEqual(nadia.call('GET', '/api/chats')[0], 401)
        self.assertEqual(Browser(self).call('POST', '/api/login', {'username': 'nadia', 'password': GOOD + ' two'})[0], 401)
        self.assertEqual(Browser(self).call('POST', '/api/login', {'username': 'nadia', 'password': temporary})[0], 200)

    def test_password_change_signs_out_other_devices_only(self):
        admin = self.admin()
        laptop = admin
        phone = Browser(self)
        phone.call('POST', '/api/login', {'username': 'owner', 'password': GOOD})
        self.assertEqual(laptop.call('POST', '/api/password', {'current': GOOD, 'new': GOOD + ' new'})[0], 200)
        self.assertEqual(laptop.call('GET', '/api/chats')[0], 200)
        self.assertEqual(phone.call('GET', '/api/chats')[0], 401)

    def test_repeated_wrong_passwords_lock_sign_in_then_expire(self):
        self.admin()
        now = [1000.0]
        self.accounts._clock = lambda: now[0]
        browser = Browser(self)
        for _ in range(MAX_FAILURES):
            self.assertEqual(browser.call('POST', '/api/login', {'username': 'owner', 'password': 'not the password'})[1]['code'], 'bad_credentials')
        self.assertEqual(browser.call('POST', '/api/login', {'username': 'owner', 'password': GOOD})[1]['code'], 'locked')
        now[0] += FAILURE_WINDOW + 1
        self.assertEqual(browser.call('POST', '/api/login', {'username': 'owner', 'password': GOOD})[0], 200)

    def test_wrong_user_and_wrong_password_look_the_same(self):
        self.admin()
        browser = Browser(self)
        self.assertEqual(browser.call('POST', '/api/login', {'username': 'nobody', 'password': 'not the password'}),
                         browser.call('POST', '/api/login', {'username': 'owner', 'password': 'not the password'}))

    def test_expired_and_forged_sessions_are_refused(self):
        browser = self.admin()
        real = self.accounts._clock
        self.accounts._clock = lambda: real() + 15 * 24 * 3600
        self.assertEqual(browser.call('GET', '/api/chats')[0], 401)
        self.accounts._clock = real
        for forged in ['moriq_session=aaaaaaaa', 'moriq_session=' + 'a' * 500, 'moriq_session="; DROP TABLE users', 'bad\x00cookie']:
            fake = Browser(self)
            fake.cookie = forged
            self.assertEqual(fake.call('GET', '/api/chats')[0], 401, forged)

    def test_activity_log_has_no_secrets_or_chat_text(self):
        admin = self.admin()
        chat = admin.call('POST', '/api/chats', {'workspace': 'architecture'})[1]['id']
        admin.call('POST', '/api/ask', {'chat': chat, 'message': 'A private client question about a roof'})
        Browser(self).call('POST', '/api/login', {'username': 'owner', 'password': 'wrong password here'})
        log = json.dumps(self.accounts.activity())
        self.assertIn('sign_in_failed', log)
        self.assertNotIn('private client', log)
        self.assertNotIn('wrong password here', log)
        self.assertNotIn(GOOD, log)

    def test_password_rules_and_hashing(self):
        for bad in ['short', 'aaaaaaaaaaaa', 'password123', 'x' * 300, None, 12345678901]:
            with self.assertRaises(AccountError):
                check_password(bad)
        with self.assertRaises(AccountError):
            check_password('nadia-is-great', 'nadia')
        stored = hash_password(GOOD)
        self.assertTrue(verify_password(GOOD, stored))
        self.assertFalse(verify_password('wrong', stored))
        self.assertNotEqual(stored, hash_password(GOOD))
        self.assertFalse(verify_password(GOOD, 'garbage'))

    def test_username_rules(self):
        for bad in ['', 'a', 'Has Space', '../etc', '<script>', 'x' * 41, None]:
            with self.assertRaises(AccountError):
                self.accounts.create_user(bad, 'Name', GOOD)
        self.accounts.create_user('Nadia.K', 'Nadia', GOOD)
        with self.assertRaises(AccountError):
            self.accounts.create_user('nadia.k', 'Other', GOOD)


class MigrationTest(unittest.TestCase):
    def test_chats_from_before_accounts_go_to_the_first_admin(self):
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / 'chats.sqlite3')
            old = sqlite3.connect(path)
            old.executescript(
                '''CREATE TABLE chats(id TEXT PRIMARY KEY, title TEXT NOT NULL, workspace TEXT NOT NULL, updated REAL NOT NULL);
                   CREATE TABLE messages(seq INTEGER PRIMARY KEY AUTOINCREMENT, chat TEXT NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
                     role TEXT NOT NULL, text TEXT NOT NULL, meta TEXT NOT NULL);
                   INSERT INTO chats VALUES('aaaa', 'Old chat', 'architecture', 1);
                   INSERT INTO messages(chat, role, text, meta) VALUES('aaaa', 'user', 'Old question', '{}');''')
            old.close()
            store = Store(path)
            accounts = Accounts(store)
            first = accounts.create_user('owner', 'Owner', GOOD, 'admin')
            second = accounts.create_user('nadia', 'Nadia', GOOD)
            self.assertEqual(store.get('aaaa', first['id'])['messages'][0]['text'], 'Old question')
            self.assertIsNone(store.get('aaaa', second['id']))
            store.close()


class HostedTest(AuthCase):
    config = Config({'moriq.example.com'}, setup_code='correct-setup-code')

    def test_setup_needs_the_code_when_hosted(self):
        browser = Browser(self, 'moriq.example.com', 'https://moriq.example.com')
        self.assertTrue(browser.call('GET', '/api/session')[1]['setup_code_required'])
        form = {'username': 'owner', 'name': 'Owner', 'password': GOOD}
        self.assertEqual(browser.call('POST', '/api/setup', form)[1]['code'], 'bad_setup_code')
        self.assertEqual(browser.call('POST', '/api/setup', {**form, 'code': 'wrong'})[1]['code'], 'bad_setup_code')
        self.assertEqual(browser.call('POST', '/api/setup', {**form, 'code': 'correct-setup-code'})[0], 201)
        self.assertIn('Secure', browser.set_cookie)

    def test_setup_code_guessing_is_limited(self):
        browser = Browser(self, 'moriq.example.com')
        form = {'username': 'owner', 'name': 'Owner', 'password': GOOD, 'code': 'wrong'}
        for _ in range(MAX_FAILURES):
            browser.call('POST', '/api/setup', form)
        self.assertEqual(browser.call('POST', '/api/setup', {**form, 'code': 'correct-setup-code'})[1]['code'], 'locked')

    def test_only_the_configured_site_is_accepted(self):
        self.assertEqual(Browser(self, 'evil.example.com').call('GET', '/')[0], 403)
        self.assertEqual(Browser(self, 'moriq.example.com', 'https://evil.example.com').call('POST', '/api/login', {})[0], 403)
        self.assertEqual(Browser(self, 'moriq.example.com', 'http://moriq.example.com').call('POST', '/api/login', {})[0], 403)
        self.assertEqual(Browser(self, 'moriq.example.com').call('GET', '/')[0], 200)


if __name__ == '__main__':
    unittest.main()
