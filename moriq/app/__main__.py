"""Run with: py -3.12 -m moriq.app"""

import os
from pathlib import Path

from moriq.app.corpus import build_registry
from moriq.app.provider import OllamaProvider
from moriq.app.server import Service, make_server
from moriq.app.store import Store


def main():
    home = Path(os.environ.get('MORIQ_HOME', Path.home() / '.moriq'))
    home.mkdir(parents=True, exist_ok=True)
    port = int(os.environ.get('MORIQ_PORT', '5180'))
    server = make_server(Service(Store(str(home / 'chats.sqlite3')), build_registry(), OllamaProvider()), port)
    print(f'MORIQ AI: http://127.0.0.1:{port}  (local only; press Ctrl+C to stop)', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
