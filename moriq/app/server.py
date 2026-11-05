"""MORIQ AI app: pages plus a JSON API, with accounts. Standard library only.

It listens on 127.0.0.1. To host it for a team, keep it there behind an HTTPS reverse proxy
and set MORIQ_ALLOWED_HOSTS. See docs/moriq-project/DEPLOYMENT-AND-SECURITY.md.
"""

import hmac
import json
import os
import re
import secrets
import threading
import uuid
from dataclasses import dataclass, field
from http.cookies import CookieError, SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from moriq.app.auth import SESSION_SECONDS, AccountError, Accounts
from moriq.app.pipeline import MAX_MESSAGE, OUT_OF_SCOPE, OUT_OF_SCOPE_MARK, build_messages, decide, finish
from moriq.app.profile import PROFILE, WORKSPACES, profile_text
from moriq.app.provider import ProviderUnavailable

ROOT = Path(__file__).resolve().parent
STUDIO = ROOT.parents[1] / 'studio-preview'
STATIC = {
    '/': (ROOT / 'web' / 'index.html', 'text/html; charset=utf-8'),
    '/app.js': (ROOT / 'web' / 'app.js', 'text/javascript; charset=utf-8'),
    '/styles.css': (ROOT / 'web' / 'ios.css', 'text/css; charset=utf-8'),
    '/chat.css': (ROOT / 'web' / 'chat.css', 'text/css; charset=utf-8'),
    '/answer.js': (ROOT / 'web' / 'answer.js', 'text/javascript; charset=utf-8'),
    '/facts.js': (ROOT / 'web' / 'facts.js', 'text/javascript; charset=utf-8'),
    '/welcome.css': (ROOT / 'web' / 'welcome.css', 'text/css; charset=utf-8'),
    '/welcome.js': (ROOT / 'web' / 'welcome.js', 'text/javascript; charset=utf-8'),
    **{f'/projects/{name}.jpg': (ROOT / 'web' / 'projects' / f'{name}.jpg', 'image/jpeg')
       for name in ('villa-430', 'amwaj-villa', 'aak-villa', 'meenakshi-bamboos', 'apartment-11')},
    '/sw.js': (ROOT / 'web' / 'sw.js', 'text/javascript; charset=utf-8'),
    '/manifest.webmanifest': (ROOT / 'web' / 'manifest.webmanifest', 'application/manifest+json'),
    '/icons/icon.svg': (ROOT / 'web' / 'icon.svg', 'image/svg+xml'),
    '/assets/courtyard-villa.jpg': (STUDIO / 'assets' / 'courtyard-villa.jpg', 'image/jpeg'),
    **{f'/icons/icon-{name}.png': (ROOT / 'web' / 'icons' / f'icon-{name}.png', 'image/png')
       for name in ('180', '192', '512', 'maskable-512')},
}
CSP = ("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self'; connect-src 'self'; "
       "object-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'")
MAX_BODY = 32768
ID = re.compile(r'[0-9a-f]{32}')
CHAT_PATH = re.compile(r'/api/chats/([0-9a-f]{32})')
USER_PATH = re.compile(r'/api/users/([0-9a-f]{32})/(active|reset)')
COOKIE = 'moriq_session'
QUEUE_SECONDS = 180
PUBLIC = {'claim_status': 'not_assessed', 'release_allowed': False}


@dataclass
class Config:
    allowed_hosts: set = field(default_factory=set)  # Public host names when hosted behind HTTPS.
    trust_proxy: bool = False
    setup_code: str = ''

    @property
    def hosted(self):
        return bool(self.allowed_hosts)

    @classmethod
    def from_env(cls):
        hosts = {h.strip().lower() for h in os.environ.get('MORIQ_ALLOWED_HOSTS', '').split(',') if h.strip()}
        return cls(hosts, trust_proxy=os.environ.get('MORIQ_TRUST_PROXY') == '1')


class Service:
    """Runs one model answer at a time, because a CPU-only machine cannot do more. Others wait in a queue."""

    def __init__(self, store, registry, provider, knowledge=None):
        self.store, self.registry, self.provider, self.knowledge = store, registry, provider, knowledge
        self.accounts = Accounts(store)
        self.lock = threading.Lock()
        self.active = {}
        self.run = threading.Semaphore(1)
        self.queue_seconds = QUEUE_SECONDS

    def cancel(self, request_id, user_id):
        with self.lock:
            entry = self.active.get(request_id)
        if entry is None or entry[1] != user_id:
            return False
        entry[0].set()
        return True


def _clean(value, limit):
    return value.strip()[:limit] if type(value) is str else ''


def chat_events(service, body, user):
    """Yield public events for one question, saving only what the user was shown."""
    owner = user['id']
    chat_id, text = body.get('chat'), _clean(body.get('message'), MAX_MESSAGE + 1)
    if type(chat_id) is not str or not ID.fullmatch(chat_id) or service.store.get(chat_id, owner) is None:
        yield {'type': 'error', 'code': 'unknown_chat', **PUBLIC}
        return
    if not text or len(text) > MAX_MESSAGE:
        yield {'type': 'error', 'code': 'invalid_message', **PUBLIC}
        return
    level = 'freshie' if body.get('level') == 'freshie' else 'standard'
    history = service.store.history(chat_id, owner)
    decision = decide(text, service.registry, service.knowledge, jurisdiction=_clean(body.get('jurisdiction'), 80),
                      edition=_clean(body.get('edition'), 80), has_answer=any(role == 'assistant' for role, _ in history))
    if not service.store.append(chat_id, 'user', text):
        yield {'type': 'error', 'code': 'chat_full', **PUBLIC}
        return
    chat = service.store.get(chat_id, owner)
    if chat['title'] == 'New chat':
        service.store.rename(chat_id, owner, text)
    if decision.action == 'profile':
        meta = {'status': 'profile', 'label': 'public_profile', 'links': PROFILE['facts'], **PUBLIC}
        service.store.append(chat_id, 'assistant', profile_text(), meta)
        yield {'type': 'done', 'text': profile_text(), **meta}
        return
    if decision.action == 'intro':
        meta = {'status': 'intro', 'code': 'none', 'label': 'intro', **PUBLIC}
        service.store.append(chat_id, 'assistant', decision.message, meta)
        yield {'type': 'done', 'text': decision.message, **meta}
        return
    if decision.action == 'blocked':
        label = 'out_of_scope' if decision.code == 'out_of_scope' else 'evidence_gap'
        meta = {'status': 'blocked', 'code': decision.code, 'label': label, **PUBLIC}
        service.store.append(chat_id, 'assistant', decision.message, meta)
        yield {'type': 'done', 'text': decision.message, **meta}
        return
    if not service.run.acquire(blocking=False):
        yield {'type': 'queued', **PUBLIC}
        if not service.run.acquire(timeout=service.queue_seconds):
            yield {'type': 'error', 'code': 'busy', **PUBLIC}
            return
    request_id = uuid.uuid4().hex
    cancelled = threading.Event()
    with service.lock:
        service.active[request_id] = (cancelled, owner)
    pieces = []
    meta = {'status': 'failed', 'code': 'model_unavailable', 'label': 'failed', **PUBLIC}
    stream = None
    declined = False
    try:
        titles = [h.chunk.provenance.metadata.title for h in decision.hits] + [n.title for n in decision.notes]
        yield {'type': 'start', 'request_id': request_id, 'category': decision.category, 'sources': titles, **PUBLIC}
        stream = service.provider.stream(build_messages(decision, text, history, level, chat['workspace']), cancelled)
        released = False
        for piece in stream:
            pieces.append(piece)
            if not released:
                # Hold the first characters so a scope refusal never reaches the screen.
                held = ''.join(pieces).lstrip()
                if held.startswith(OUT_OF_SCOPE_MARK):
                    declined = True
                    break
                if OUT_OF_SCOPE_MARK.startswith(held):
                    continue
                released = True
                piece = ''.join(pieces)
            yield {'type': 'token', 'text': piece}
            if cancelled.is_set():
                break
        answer = ''.join(pieces)
        if declined:
            pieces = [OUT_OF_SCOPE]
            meta = {'status': 'blocked', 'code': 'out_of_scope', 'label': 'out_of_scope', 'text': OUT_OF_SCOPE, **PUBLIC}
        elif cancelled.is_set():
            meta = {'status': 'cancelled', 'code': 'none', 'label': 'stopped', **PUBLIC}
        elif not answer.strip():
            meta = {'status': 'failed', 'code': 'empty_response', 'label': 'failed', **PUBLIC}
        else:
            meta = {'status': 'draft', 'code': 'none', **finish(decision, answer, service.registry), **PUBLIC}
    except ProviderUnavailable:
        pass
    except GeneratorExit:
        cancelled.set()
        meta = {'status': 'cancelled', 'code': 'client_left', 'label': 'stopped', **PUBLIC}
        service.store.append(chat_id, 'assistant', ''.join(pieces), meta)
        raise
    finally:
        if stream is not None:
            stream.close()
        with service.lock:
            service.active.pop(request_id, None)
        service.run.release()
    service.store.append(chat_id, 'assistant', ''.join(pieces), meta)
    yield {'type': 'done', **meta}


class Handler(BaseHTTPRequestHandler):
    server_version = 'MORIQ'
    sys_version = ''
    protocol_version = 'HTTP/1.1'

    def log_message(self, *_):  # Requests can contain chat text; do not log them.
        pass

    @property
    def service(self):
        return self.server.service

    @property
    def config(self):
        return self.server.config

    def _allowed(self):
        port = self.server.server_address[1]
        local = {f'127.0.0.1:{port}', f'localhost:{port}'}
        # Only for a local scanner reaching the app from a container, such as host.docker.internal.
        if os.environ.get('MORIQ_SCAN_HOST'):
            local.add(f"{os.environ['MORIQ_SCAN_HOST']}:{port}")
        host = (self.headers.get('Host') or '').lower()
        if host not in local and host not in self.config.allowed_hosts:
            return False
        origin = self.headers.get('Origin')
        origins = {f'http://{a}' for a in local} | {f'https://{a}' for a in self.config.allowed_hosts}
        return origin is None or origin.lower() in origins

    def _client(self):
        if self.config.trust_proxy:
            forwarded = self.headers.get('X-Forwarded-For')
            if forwarded:
                return forwarded.split(',')[-1].strip()[:64]
        return self.client_address[0]

    def _token(self):
        try:
            morsel = SimpleCookie(self.headers.get('Cookie') or '').get(COOKIE)
        except CookieError:
            return None
        return morsel.value if morsel else None

    def _user(self):
        return self.service.accounts.session_user(self._token())

    def _cookie_value(self, token, age):
        secure = '; Secure' if self.config.hosted else ''
        return f'{COOKIE}={token}; Path=/; HttpOnly; SameSite=Strict; Max-Age={age}{secure}'

    def _headers(self, status, kind, length=None, cookie=None):
        self.send_response(status)
        self.send_header('Content-Type', kind)
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Content-Security-Policy', CSP)
        if self.config.hosted:
            self.send_header('Strict-Transport-Security', 'max-age=31536000')
        if cookie:
            self.send_header('Set-Cookie', cookie)
        if length is None:
            self.send_header('Connection', 'close')
            self.close_connection = True
        else:
            self.send_header('Content-Length', str(length))
        self.end_headers()

    def _json(self, status, value, cookie=None):
        data = json.dumps(value).encode('utf-8')
        self._headers(status, 'application/json', len(data), cookie)
        self.wfile.write(data)

    def _body(self):
        if self.headers.get_content_type() != 'application/json':
            return None
        try:
            length = int(self.headers.get('Content-Length', ''))
        except ValueError:
            return None
        if not 0 <= length <= MAX_BODY:
            self.close_connection = True
            return None
        try:
            value = json.loads(self.rfile.read(length))
        except ValueError:
            return None
        return value if type(value) is dict else None

    def _require_user(self, allow_must_change=False):
        """Return the signed-in user, or send the refusal and return None."""
        user = self._user()
        if user is None:
            self._json(401, {'code': 'signed_out'})
            return None
        if user['must_change'] and not allow_must_change:
            self._json(403, {'code': 'password_change_required'})
            return None
        return user

    def _session_state(self, user):
        accounts = self.service.accounts
        needs_setup = accounts.needs_setup()
        return {'user': user, 'needs_setup': needs_setup, 'setup_code_required': needs_setup and self.config.hosted}

    def do_GET(self):
        if not self._allowed():
            return self._json(403, {'code': 'denied'})
        route = self.path.split('?', 1)[0]
        if route == '/favicon.ico':  # No approved logo exists to use as an icon.
            self.send_response(204)
            self.send_header('Content-Length', '0')
            return self.end_headers()
        if route in STATIC:
            path, kind = STATIC[route]
            try:
                data = path.read_bytes()
            except OSError:
                return self._json(404, {'code': 'not_found'})
            self._headers(200, kind, len(data))
            return self.wfile.write(data)
        if route == '/api/health':
            return self._json(200, {'app': 'moriq-ai'})
        if route == '/api/session':
            return self._json(200, self._session_state(self._user()))
        if not route.startswith('/api/'):
            return self._json(404, {'code': 'not_found'})
        user = self._require_user()
        if user is None:
            return None
        if route == '/api/status':
            provider = self.service.provider
            documents = bool(self.service.knowledge and self.service.knowledge.has_documents)
            return self._json(200, {'model': provider.name, 'model_label': provider.label,
                                    'model_ready': provider.available(), 'documents_loaded': documents,
                                    'workspaces': WORKSPACES, 'profile': PROFILE, **PUBLIC})
        if route == '/api/chats':
            return self._json(200, {'chats': self.service.store.list_chats(user['id'])})
        if route == '/api/users':
            if user['role'] != 'admin':
                return self._json(403, {'code': 'denied'})
            return self._json(200, {'users': self.service.accounts.list_users()})
        match = CHAT_PATH.fullmatch(route)
        if match:
            chat = self.service.store.get(match[1], user['id'])
            return self._json(200, chat) if chat else self._json(404, {'code': 'not_found'})
        return self._json(404, {'code': 'not_found'})

    def _login(self, body):
        accounts = self.service.accounts
        try:
            token, user = accounts.login(body.get('username'), body.get('password'), self._client())
        except AccountError as exc:
            return self._json(429 if exc.code == 'locked' else 401, {'code': exc.code})
        return self._json(200, self._session_state(user), self._cookie_value(token, SESSION_SECONDS))

    def _setup(self, body):
        accounts, client = self.service.accounts, self._client()
        if not accounts.needs_setup():
            return self._json(409, {'code': 'already_set_up'})
        if self.config.hosted:
            code = body.get('code')
            if accounts.blocked_setup(client):
                return self._json(429, {'code': 'locked'})
            if type(code) is not str or not self.config.setup_code or not hmac.compare_digest(code.strip().encode(), self.config.setup_code.encode()):
                accounts.record_setup_failure(client)
                return self._json(401, {'code': 'bad_setup_code'})
        try:
            user = accounts.create_user(body.get('username'), body.get('name'), body.get('password'), 'admin', actor='first run')
        except AccountError as exc:
            return self._json(400, {'code': exc.code})
        token, user = accounts.start_session(user['id'], user['username'])
        return self._json(201, self._session_state(user), self._cookie_value(token, SESSION_SECONDS))

    def do_POST(self):
        if not self._allowed():
            return self._json(403, {'code': 'denied'})
        body = self._body()
        if body is None:
            return self._json(400, {'code': 'invalid_request'})
        route = self.path.split('?', 1)[0]
        if route == '/api/login':
            return self._login(body)
        if route == '/api/setup':
            return self._setup(body)
        if route == '/api/logout':
            self.service.accounts.logout(self._token())
            return self._json(200, {}, self._cookie_value('', 0))
        if route == '/api/password':
            user = self._require_user(allow_must_change=True)
            if user is None:
                return None
            try:
                self.service.accounts.change_password(user, body.get('current'), body.get('new'), self._token())
            except AccountError as exc:
                return self._json(400, {'code': exc.code})
            return self._json(200, self._session_state(self._user()))
        user = self._require_user()
        if user is None:
            return None
        if route == '/api/chats':
            workspace = body.get('workspace')
            if workspace not in {w['id'] for w in WORKSPACES}:
                return self._json(400, {'code': 'invalid_request'})
            chat = self.service.store.create(user['id'], workspace)
            return self._json(201, chat) if chat else self._json(409, {'code': 'chat_limit'})
        if route == '/api/ask':
            self._headers(200, 'application/x-ndjson')
            events = chat_events(self.service, body, user)
            try:
                for event in events:
                    self.wfile.write((json.dumps(event) + '\n').encode('utf-8'))
                    self.wfile.flush()
            except OSError:
                events.close()
            return None
        if route == '/api/cancel':
            request_id = body.get('request_id')
            done = type(request_id) is str and self.service.cancel(request_id, user['id'])
            return self._json(200 if done else 404, {'cancelled': done})
        if route == '/api/users' or USER_PATH.fullmatch(route):
            return self._admin(route, body, user)
        return self._json(404, {'code': 'not_found'})

    def _admin(self, route, body, user):
        if user['role'] != 'admin':
            return self._json(403, {'code': 'denied'})
        accounts = self.service.accounts
        try:
            if route == '/api/users':
                temporary = secrets.token_urlsafe(12)
                role = 'admin' if body.get('role') == 'admin' else 'member'
                created = accounts.create_user(body.get('username'), body.get('name'), temporary, role, True, user['username'])
                return self._json(201, {'user': created, 'temporary_password': temporary})
            match = USER_PATH.fullmatch(route)
            if match[2] == 'active':
                return self._json(200, {'user': accounts.set_active(user, match[1], body.get('active') is True)})
            return self._json(200, {'temporary_password': accounts.reset_password(user['username'], match[1])})
        except AccountError as exc:
            return self._json(404 if exc.code == 'not_found' else 400, {'code': exc.code})

    def do_PATCH(self):
        if not self._allowed():
            return self._json(403, {'code': 'denied'})
        user = self._require_user()
        if user is None:
            return None
        body, match = self._body(), CHAT_PATH.fullmatch(self.path)
        title = _clean((body or {}).get('title'), 60)
        if not match or not title:
            return self._json(400, {'code': 'invalid_request'})
        return self._json(200 if self.service.store.rename(match[1], user['id'], title) else 404, {'title': title})

    def do_DELETE(self):
        if not self._allowed():
            return self._json(403, {'code': 'denied'})
        user = self._require_user()
        if user is None:
            return None
        match = CHAT_PATH.fullmatch(self.path)
        if not match:
            return self._json(400, {'code': 'invalid_request'})
        return self._json(200 if self.service.store.delete(match[1], user['id']) else 404, {})


class Server(ThreadingHTTPServer):
    def handle_error(self, request, client_address):
        # A browser closing mid-answer is normal. Anything else must not print request details either.
        pass


def make_server(service, port=5180, config=None):
    server = Server(('127.0.0.1', port), Handler)
    server.daemon_threads = True
    server.service = service
    server.config = config or Config()
    return server
