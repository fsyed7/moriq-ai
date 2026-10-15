"""Ollama-shaped HTTP protocol against a self-owned fake listener ONLY.

No endpoint argument, live mode, tools, proxy support or real model identifier.
The parent process owns deadlines and termination, including blocked HTTP reads.
"""

import http.client
import json
import os
import socket
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

MODEL = 'moriq-offline-fixture'
LIMIT = 32768


def unique(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError('Duplicate key')
        value[key] = item
    return value


def decode(data):
    return json.loads(data, object_pairs_hook=unique, parse_constant=reject_constant)


def reject_constant(_):
    raise ValueError('Nonfinite JSON')


def validate_fixture(value):
    if (
        type(value) is not dict
        or set(value) != {'status', 'body', 'behavior'}
        or type(value['status']) is not int
        or value['status'] not in {200, 302, 500}
        or type(value['body']) is not str
        or len(value['body'].encode()) > LIMIT
        or value['behavior']
        not in {
            'normal',
            'block',
            'slow',
            'disconnect',
            'oversize',
            'refused',
            'noise',
            'delayed',
            'bad_type',
            'encoding',
            'transfer',
            'duplicate_length',
            'short_body',
        }
    ):
        raise ValueError('Invalid fake fixture')
    return value


def request_body(request):
    if (
        type(request) is not dict
        or set(request) != {'instruction', 'question', 'untrusted_evidence'}
        or any(type(request[k]) is not str or not request[k].strip() for k in ('instruction', 'question'))
        or type(request['untrusted_evidence']) is not list
        or len(request['untrusted_evidence']) > 16
    ):
        raise ValueError('Invalid gate request')
    for source in request['untrusted_evidence']:
        if (
            type(source) is not dict
            or set(source) != {'id', 'text'}
            or any(type(v) is not str for v in source.values())
        ):
            raise ValueError('Invalid evidence')
    result = {
        'model': MODEL,
        'stream': False,
        'messages': [
            {'role': 'system', 'content': request['instruction']},
            {
                'role': 'user',
                'content': json.dumps(
                    {'question': request['question'], 'untrusted_evidence': request['untrusted_evidence']}
                ),
            },
        ],
        'options': {'num_gpu': 0, 'num_predict': 600, 'temperature': 0},
        'keep_alive': 0,
    }
    raw = json.dumps(result, allow_nan=False).encode()
    if len(raw) > LIMIT:
        raise ValueError('Request too large')
    return raw


def response_text(raw):
    if len(raw) > LIMIT:
        raise ValueError('Response too large')
    value = decode(raw)
    if (
        type(value) is not dict
        or set(value) != {'model', 'message', 'done', 'done_reason'}
        or value['model'] != MODEL
        or value['done'] is not True
        or value['done_reason'] != 'stop'
        or type(value['message']) is not dict
        or set(value['message']) != {'role', 'content'}
        or value['message']['role'] != 'assistant'
        or type(value['message']['content']) is not str
        or not value['message']['content'].strip()
    ):
        raise ValueError('Incomplete or unsupported reply')
    return value['message']['content']


class FixtureServer(HTTPServer):
    def handle_error(self, request, client_address):
        # Fixture errors must never print a traceback containing a request.
        pass


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        length = int(self.headers.get('Content-Length', '-1'))
        if self.path != '/api/chat' or not 0 <= length <= LIMIT or self.rfile.read(length) != self.server.expected:
            self.send_error(400)
            return
        fixture = self.server.fixture
        behavior = fixture['behavior']
        if behavior == 'disconnect':
            return
        if behavior == 'noise':
            os.write(2, b'PRIVATE_HTTP_LOG')
        if behavior == 'block':
            time.sleep(60)
        if behavior == 'delayed':
            time.sleep(0.5)
        self.send_response(fixture['status'])
        self.send_header('Content-Type', 'text/html' if behavior == 'bad_type' else 'application/json')
        self.send_header('Connection', 'close')
        extra_headers = {
            'encoding': [('Content-Encoding', 'gzip')],
            'transfer': [('Transfer-Encoding', 'chunked')],
            'duplicate_length': [('Content-Length', '1'), ('Content-Length', '2')],
            'short_body': [('Content-Length', str(len(fixture['body'].encode()) + 10))],
        }
        for name, value in extra_headers.get(behavior, []):
            self.send_header(name, value)
        if fixture['status'] == 302:
            self.send_header('Location', 'http://127.0.0.1:11434/api/chat')
        self.end_headers()
        if behavior == 'slow':
            while True:
                self.wfile.write(b' ')
                self.wfile.flush()
                time.sleep(0.03)
        self.wfile.write(b'X' * (LIMIT + 1) if behavior == 'oversize' else fixture['body'].encode())


def exchange(request, fixture):
    expected = request_body(request)
    fixture = validate_fixture(fixture)
    # The only destination is this freshly bound listener, never caller configuration.
    with FixtureServer(('127.0.0.1', 0), Handler) as server:
        server.expected, server.fixture = expected, fixture
        server.timeout = 2
        port = server.server_port
        thread = threading.Thread(target=server.handle_request, daemon=True)
        thread.start()
        connection = http.client.HTTPConnection('127.0.0.1', port, timeout=2)
        try:
            if fixture['behavior'] == 'refused':
                # A bound, non-listening socket deterministically refuses without contacting a service.
                with socket.socket() as closed:
                    closed.bind(('127.0.0.1', 0))
                    connection.port = closed.getsockname()[1]
                    connection.connect()
            connection.request('POST', '/api/chat', expected, {'Content-Type': 'application/json'})
            response = connection.getresponse()
            return read_response(response)
        finally:
            connection.close()
            thread.join(timeout=0.1)


def read_response(response):
    headers = response.headers
    lengths = headers.get_all('Content-Length', [])
    if (
        response.status != 200
        or headers.get_all('Content-Type') != ['application/json']
        or headers.get('Content-Encoding') is not None
        or headers.get('Transfer-Encoding') is not None
        or len(lengths) > 1
        or (lengths and (not lengths[0].isascii() or not lengths[0].isdigit() or int(lengths[0]) > LIMIT))
    ):
        raise ValueError('Unsupported HTTP response')
    raw = response.read(LIMIT + 1)
    if lengths and len(raw) != int(lengths[0]):
        raise ValueError('Truncated HTTP response')
    return response_text(raw)


def main():
    data = decode(sys.stdin.buffer.read(65537))
    if type(data) is not dict or set(data) != {'request', 'scenario', 'reply'} or data['scenario'] != 'success':
        raise ValueError('Invalid worker protocol')
    text = exchange(data['request'], decode(data['reply']))
    os.write(1, json.dumps({'done': True, 'text': text}).encode())


if __name__ == '__main__':
    try:
        main()
    except Exception:
        # No exception text, HTTP body or tracebacks on either process pipe.
        sys.exit(1)
