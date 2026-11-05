"""Run with: py -3.12 -m moriq.app"""

import os
import secrets
from pathlib import Path

from moriq.app.corpus import build_registry
from moriq.app.knowledge import Knowledge
from moriq.app.provider import make_provider
from moriq.app.server import Config, Service, make_server
from moriq.app.store import Store


def main():
    home = Path(os.environ.get('MORIQ_HOME', Path.home() / '.moriq'))
    documents = home / 'documents'
    documents.mkdir(parents=True, exist_ok=True)
    port = int(os.environ.get('MORIQ_PORT', '5180'))
    provider = make_provider()
    service = Service(Store(str(home / 'chats.sqlite3')), build_registry(), provider, Knowledge(documents))
    config = Config.from_env()
    code_file = home / 'setup-code.txt'
    if config.hosted and service.accounts.needs_setup():
        # A hosted server must not hand the admin account to whoever visits first.
        config.setup_code = secrets.token_urlsafe(12)
        code_file.write_text(config.setup_code, encoding='utf-8')
        print(f'First-run setup code: {config.setup_code} (also in {code_file})', flush=True)
    else:
        code_file.unlink(missing_ok=True)
    server = make_server(service, port, config)
    print(f'MORIQ AI: http://127.0.0.1:{port}  (model: {provider.label}; press Ctrl+C to stop)', flush=True)
    print(f'MORIQ documents folder: {documents}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
