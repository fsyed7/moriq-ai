"""MORIQ AI local app: Studio pages plus a JSON API on 127.0.0.1. Standard library only.

Trusted single-user prototype. It has no login and must not be exposed beyond this machine.
"""

import json
import re
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from moriq.app.pipeline import MAX_MESSAGE, OUT_OF_SCOPE, OUT_OF_SCOPE_MARK, build_messages, decide, finish
from moriq.app.profile import PROFILE, WORKSPACES, profile_text
from moriq.app.provider import ProviderUnavailable

ROOT = Path(__file__).resolve().parent
STUDIO = ROOT.parents[1] / 'studio-preview'
STATIC = {
    '/': (ROOT / 'web' / 'index.html', 'text/html; charset=utf-8'),
    '/app.js': (ROOT / 'web' / 'app.js', 'text/javascript; charset=utf-8'),
    '/live.css': (ROOT / 'web' / 'live.css', 'text/css; charset=utf-8'),
    '/styles.css': (STUDIO / 'styles.css', 'text/css; charset=utf-8'),
    '/assets/courtyard-villa.jpg': (STUDIO / 'assets' / 'courtyard-villa.jpg', 'image/jpeg'),
}
CSP = ("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self'; connect-src 'self'; "
       "object-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'")
MAX_BODY = 32768
ID = re.compile(r'[0-9a-f]{32}')
CHAT_PATH = re.compile(r'/api/chats/([0-9a-f]{32})')
PUBLIC = {'claim_status': 'not_assessed', 'release_allowed': False}


class Service:
    """Holds one model run at a time, because this machine has no GPU."""

    def __init__(self, store, registry, provider, knowledge=None):
        self.store, self.registry, self.provider, self.knowledge = store, registry, provider, knowledge
        self.lock = threading.Lock()
        self.active = {}
        self.run = threading.Semaphore(1)

    def cancel(self, request_id):
        with self.lock:
            event = self.active.get(request_id)
        if event is None:
            return False
        event.set()
        return True


def _clean(value, limit):
    return value.strip()[:limit] if type(value) is str else ''


def chat_events(service, body):
    """Yield public events for one question, saving only what the user was shown."""
    chat_id, text = body.get('chat'), _clean(body.get('message'), MAX_MESSAGE + 1)
    if type(chat_id) is not str or not ID.fullmatch(chat_id) or service.store.get(chat_id) is None:
        yield {'type': 'error', 'code': 'unknown_chat', **PUBLIC}
        return
    if not text or len(text) > MAX_MESSAGE:
        yield {'type': 'error', 'code': 'invalid_message', **PUBLIC}
        return
    level = 'freshie' if body.get('level') == 'freshie' else 'standard'
    decision = decide(text, service.registry, service.knowledge, jurisdiction=_clean(body.get('jurisdiction'), 80),
                      edition=_clean(body.get('edition'), 80))
    history = service.store.history(chat_id)
    if not service.store.append(chat_id, 'user', text):
        yield {'type': 'error', 'code': 'chat_full', **PUBLIC}
        return
    chat = service.store.get(chat_id)
    if chat['title'] == 'New chat':
        service.store.rename(chat_id, text)
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
        yield {'type': 'error', 'code': 'busy', **PUBLIC}
        return
    request_id = uuid.uuid4().hex
    cancelled = threading.Event()
    with service.lock:
        service.active[request_id] = cancelled
    pieces = []
    meta = {'status': 'failed', 'code': 'model_unavailable', 'label': 'failed', **PUBLIC}
    stream = None
    declined = False
    try:
        yield {'type': 'start', 'request_id': request_id, 'category': decision.category, **PUBLIC}
        stream = service.provider.stream(build_messages(decision, text, history, level), cancelled)
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

    def _allowed(self):
        port = self.server.server_address[1]
        allowed = {f'127.0.0.1:{port}', f'localhost:{port}'}
        if self.headers.get('Host') not in allowed:
            return False
        origin = self.headers.get('Origin')
        return origin is None or origin in {f'http://{a}' for a in allowed}

    def _headers(self, status, kind, length=None):
        self.send_response(status)
        self.send_header('Content-Type', kind)
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', CSP)
        if length is None:
            self.send_header('Connection', 'close')
            self.close_connection = True
        else:
            self.send_header('Content-Length', str(length))
        self.end_headers()

    def _json(self, status, value):
        data = json.dumps(value).encode('utf-8')
        self._headers(status, 'application/json', len(data))
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
        if route == '/api/status':
            provider = self.service.provider
            documents = bool(self.service.knowledge and self.service.knowledge.has_documents)
            return self._json(200, {'model': provider.name, 'model_label': provider.label,
                                    'model_ready': provider.available(), 'documents_loaded': documents,
                                    'workspaces': WORKSPACES, 'profile': PROFILE, **PUBLIC})
        if route == '/api/chats':
            return self._json(200, {'chats': self.service.store.list_chats()})
        match = CHAT_PATH.fullmatch(route)
        if match:
            chat = self.service.store.get(match[1])
            return self._json(200, chat) if chat else self._json(404, {'code': 'not_found'})
        return self._json(404, {'code': 'not_found'})

    def do_POST(self):
        if not self._allowed():
            return self._json(403, {'code': 'denied'})
        body = self._body()
        if body is None:
            return self._json(400, {'code': 'invalid_request'})
        route = self.path.split('?', 1)[0]
        if route == '/api/chats':
            workspace = body.get('workspace')
            if workspace not in {w['id'] for w in WORKSPACES}:
                return self._json(400, {'code': 'invalid_request'})
            chat = self.service.store.create(workspace)
            return self._json(201, chat) if chat else self._json(409, {'code': 'chat_limit'})
        if route == '/api/ask':
            self._headers(200, 'application/x-ndjson')
            events = chat_events(self.service, body)
            try:
                for event in events:
                    self.wfile.write((json.dumps(event) + '\n').encode('utf-8'))
                    self.wfile.flush()
            except OSError:
                events.close()
            return None
        if route == '/api/cancel':
            request_id = body.get('request_id')
            done = type(request_id) is str and self.service.cancel(request_id)
            return self._json(200 if done else 404, {'cancelled': done})
        return self._json(404, {'code': 'not_found'})

    def do_PATCH(self):
        if not self._allowed():
            return self._json(403, {'code': 'denied'})
        body, match = self._body(), CHAT_PATH.fullmatch(self.path)
        title = _clean((body or {}).get('title'), 60)
        if not match or not title:
            return self._json(400, {'code': 'invalid_request'})
        return self._json(200 if self.service.store.rename(match[1], title) else 404, {'title': title})

    def do_DELETE(self):
        if not self._allowed():
            return self._json(403, {'code': 'denied'})
        match = CHAT_PATH.fullmatch(self.path)
        if not match:
            return self._json(400, {'code': 'invalid_request'})
        return self._json(200 if self.service.store.delete(match[1]) else 404, {})


def make_server(service, port=5180):
    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    server.daemon_threads = True
    server.service = service
    return server
