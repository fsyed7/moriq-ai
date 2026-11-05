"""Model providers. Claude is used when credentials and the SDK are present; otherwise the local Ollama model."""

import json
import os
import urllib.error
import urllib.request

ENDPOINT = 'http://127.0.0.1:11434'
MODEL = 'qwen3:4b-instruct-2507-q4_K_M'
OPTIONS = {'temperature': 0.2, 'num_predict': 420, 'num_ctx': 4096}
FIRST_TOKEN_TIMEOUT = 300
CLAUDE_MODEL = 'claude-opus-5-5'


class ProviderUnavailable(Exception):
    pass


class OllamaProvider:
    name = MODEL
    label = 'Local model'

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


class ClaudeProvider:
    """Sends questions to Anthropic, so nothing here stays on this computer."""

    name = CLAUDE_MODEL
    label = 'Claude (cloud)'

    def __init__(self, sdk):
        self._sdk = sdk
        self._client = sdk.Anthropic()

    def available(self):
        return True

    def stream(self, messages, cancelled):
        system = '\n\n'.join(m['content'] for m in messages if m['role'] == 'system')
        turns = [m for m in messages if m['role'] != 'system']
        try:
            # Server-side fallback re-runs a declined request on another model instead of stopping.
            with self._client.beta.messages.stream(
                model=CLAUDE_MODEL,
                max_tokens=16000,
                betas=['server-side-fallback-2026-07-01'],
                fallbacks='default',
                output_config={'effort': 'medium'},
                system=system,
                messages=turns,
            ) as stream:
                for piece in stream.text_stream:
                    if cancelled.is_set():
                        return
                    yield piece
                if stream.get_final_message().stop_reason == 'refusal':
                    raise ProviderUnavailable
        except self._sdk.AnthropicError as exc:
            raise ProviderUnavailable from exc


def make_provider():
    if os.environ.get('ANTHROPIC_API_KEY') or os.environ.get('ANTHROPIC_AUTH_TOKEN'):
        try:
            import anthropic
        except ImportError:
            return OllamaProvider()
        return ClaudeProvider(anthropic)
    return OllamaProvider()
