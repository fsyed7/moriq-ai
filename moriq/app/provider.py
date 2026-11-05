"""Local Ollama client with fixed settings. It only talks to this machine."""

import json
import urllib.error
import urllib.request

ENDPOINT = 'http://127.0.0.1:11434'
MODEL = 'qwen3:4b-instruct-2507-q4_K_M'
OPTIONS = {'temperature': 0.2, 'num_predict': 420, 'num_ctx': 4096}
FIRST_TOKEN_TIMEOUT = 300


class ProviderUnavailable(Exception):
    pass


class OllamaProvider:
    name = MODEL

    def available(self):
        try:
            with urllib.request.urlopen(f'{ENDPOINT}/api/tags', timeout=3) as response:
                names = {m.get('name') for m in json.load(response).get('models', [])}
            return MODEL in names
        except (OSError, ValueError):
            return False

    def stream(self, messages, cancelled):
        """Yield text pieces. Closing the connection asks Ollama to stop; idleness is not proven."""
        body = json.dumps({'model': MODEL, 'messages': messages, 'stream': True, 'think': False,
                           'keep_alive': '10m', 'options': OPTIONS}).encode('utf-8')
        request = urllib.request.Request(f'{ENDPOINT}/api/chat', body, {'Content-Type': 'application/json'})
        try:
            response = urllib.request.urlopen(request, timeout=FIRST_TOKEN_TIMEOUT)
        except (urllib.error.URLError, OSError) as exc:
            raise ProviderUnavailable from exc
        with response:
            for line in response:
                if cancelled.is_set():
                    return
                try:
                    chunk = json.loads(line)
                except ValueError as exc:
                    raise ProviderUnavailable from exc
                if chunk.get('error'):
                    raise ProviderUnavailable
                piece = chunk.get('message', {}).get('content', '')
                if piece:
                    yield piece
                if chunk.get('done'):
                    return
