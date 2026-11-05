"""Local SQLite chat history for one person on this machine. Not production identity or audit."""

import json
import sqlite3
import threading
import time
import uuid

LIMIT_CHATS = 200
LIMIT_MESSAGES = 400
LIMIT_TITLE = 60


class Store:
    def __init__(self, path):
        self._db = sqlite3.connect(path, check_same_thread=False)
        self._lock = threading.Lock()
        self._db.execute('PRAGMA foreign_keys=ON')
        self._db.executescript(
            '''CREATE TABLE IF NOT EXISTS chats(id TEXT PRIMARY KEY, title TEXT NOT NULL, workspace TEXT NOT NULL,
                 updated REAL NOT NULL);
               CREATE TABLE IF NOT EXISTS messages(seq INTEGER PRIMARY KEY AUTOINCREMENT,
                 chat TEXT NOT NULL REFERENCES chats(id) ON DELETE CASCADE, role TEXT NOT NULL,
                 text TEXT NOT NULL, meta TEXT NOT NULL);'''
        )
        self._db.commit()

    def close(self):
        with self._lock:
            self._db.close()

    def list_chats(self):
        with self._lock:
            rows = self._db.execute('SELECT id, title, workspace FROM chats ORDER BY updated DESC').fetchall()
        return [{'id': r[0], 'title': r[1], 'workspace': r[2]} for r in rows]

    def create(self, workspace, title='New chat'):
        with self._lock:
            if self._db.execute('SELECT COUNT(*) FROM chats').fetchone()[0] >= LIMIT_CHATS:
                return None
            chat = {'id': uuid.uuid4().hex, 'title': title[:LIMIT_TITLE], 'workspace': workspace}
            self._db.execute('INSERT INTO chats VALUES(?,?,?,?)', (chat['id'], chat['title'], workspace, time.time()))
            self._db.commit()
        return chat

    def get(self, chat_id):
        with self._lock:
            row = self._db.execute('SELECT id, title, workspace FROM chats WHERE id=?', (chat_id,)).fetchone()
            if row is None:
                return None
            messages = self._db.execute('SELECT role, text, meta FROM messages WHERE chat=? ORDER BY seq',
                                        (chat_id,)).fetchall()
        return {'id': row[0], 'title': row[1], 'workspace': row[2],
                'messages': [{'role': m[0], 'text': m[1], 'meta': json.loads(m[2])} for m in messages]}

    def rename(self, chat_id, title):
        with self._lock:
            done = self._db.execute('UPDATE chats SET title=? WHERE id=?', (title[:LIMIT_TITLE], chat_id)).rowcount
            self._db.commit()
        return bool(done)

    def delete(self, chat_id):
        with self._lock:
            done = self._db.execute('DELETE FROM chats WHERE id=?', (chat_id,)).rowcount
            self._db.commit()
        return bool(done)

    def append(self, chat_id, role, text, meta=None):
        with self._lock:
            count = self._db.execute('SELECT COUNT(*) FROM messages WHERE chat=?', (chat_id,)).fetchone()[0]
            if count >= LIMIT_MESSAGES:
                return False
            self._db.execute('INSERT INTO messages(chat, role, text, meta) VALUES(?,?,?,?)',
                             (chat_id, role, text, json.dumps(meta or {})))
            self._db.execute('UPDATE chats SET updated=? WHERE id=?', (time.time(), chat_id))
            self._db.commit()
        return True

    def history(self, chat_id):
        """Only plain drafts return to the model; blocked notices and stopped text do not."""
        chat = self.get(chat_id)
        if chat is None:
            return ()
        return tuple((m['role'], m['text']) for m in chat['messages']
                     if m['role'] == 'user' or m['meta'].get('status') == 'draft')
