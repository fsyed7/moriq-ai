"""Account tools for whoever runs the server. Example: py -3.12 -m moriq.app.admin list

Commands: add-admin USERNAME "Full Name" | reset-password USERNAME | list | activity | backup FILE
"""

import datetime
import getpass
import os
import sqlite3
import sys
from pathlib import Path

from moriq.app.auth import AccountError, Accounts
from moriq.app.store import Store


def main(argv):
    if not argv:
        sys.exit(__doc__)
    home = Path(os.environ.get('MORIQ_HOME', Path.home() / '.moriq'))
    home.mkdir(parents=True, exist_ok=True)
    store = Store(str(home / 'chats.sqlite3'))
    accounts = Accounts(store)
    command, args = argv[0], argv[1:]
    try:
        if command == 'add-admin' and len(args) == 2:
            password = getpass.getpass('New password: ')
            print('Created', accounts.create_user(args[0], args[1], password, 'admin', actor='command line')['username'])
        elif command == 'reset-password' and len(args) == 1:
            user = next((u for u in accounts.list_users() if u['username'] == args[0].lower()), None)
            if user is None:
                sys.exit('No such user.')
            print('Temporary password, shown once:', accounts.reset_password('command line', user['id']))
        elif command == 'list':
            for user in accounts.list_users():
                print(user['username'], user['role'], 'active' if user['active'] else 'disabled', user['name'])
        elif command == 'activity':
            for event in accounts.activity():
                when = datetime.datetime.fromtimestamp(event['at']).isoformat(timespec='seconds')
                print(when, event['actor'] or '-', event['action'], event['target'] or '-')
        elif command == 'backup' and len(args) == 1:
            target = sqlite3.connect(args[0])
            with target:
                store._db.backup(target)
            target.close()
            print('Backed up to', args[0])
        else:
            sys.exit(__doc__)
    except AccountError as exc:
        sys.exit(f'Failed: {exc.code}')
    finally:
        store.close()


if __name__ == '__main__':
    main(sys.argv[1:])
