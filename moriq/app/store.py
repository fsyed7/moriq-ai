"""SQLite chat history. Every chat has an owner, and owner-scoped reads return nothing for anyone else."""

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
        self._db.execute('PRAGMA journal_mode=WAL')
        self._db.executescript(
            '''CREATE TABLE IF NOT EXISTS chats(id TEXT PRIMARY KEY, title TEXT NOT NULL, workspace TEXT NOT NULL,
                 updated REAL NOT NULL);
               CREATE TABLE IF NOT EXISTS messages(seq INTEGER PRIMARY KEY AUTOINCREMENT,
                 chat TEXT NOT NULL REFERENCES chats(id) ON DELETE CASCADE, role TEXT NOT NULL,
                 text TEXT NOT NULL, meta TEXT NOT NULL);'''
        )
        columns = {row[1] for row in self._db.execute('PRAGMA table_info(chats)')}
        if 'owner' not in columns:  # Chats saved before accounts existed are claimed by the first admin.
            self._db.execute('ALTER TABLE chats ADD COLUMN owner TEXT')
        self._db.execute('CREATE INDEX IF NOT EXISTS chats_owner ON chats(owner, updated)')
        self._db.commit()

    def close(self):
        with self._lock:
            self._db.close()

    def list_chats(self, owner):
        with self._lock:
            rows = self._db.execute('SELECT id, title, workspace FROM chats WHERE owner=? ORDER BY updated DESC', (owner,)).fetchall()
        return [{'id': r[0], 'title': r[1], 'workspace': r[2]} for r in rows]

    def create(self, owner, workspace, title='New chat'):
        with self._lock:
            if self._db.execute('SELECT COUNT(*) FROM chats WHERE owner=?', (owner,)).fetchone()[0] >= LIMIT_CHATS:
                return None
            chat = {'id': uuid.uuid4().hex, 'title': title[:LIMIT_TITLE], 'workspace': workspace}
            self._db.execute('INSERT INTO chats(id, title, workspace, updated, owner) VALUES(?,?,?,?,?)',
                             (chat['id'], chat['title'], workspace, time.time(), owner))
            self._db.commit()
        return chat

    def get(self, chat_id, owner):
        with self._lock:
            row = self._db.execute('SELECT id, title, workspace FROM chats WHERE id=? AND owner=?', (chat_id, owner)).fetchone()
            if row is None:
                return None
            messages = self._db.execute('SELECT role, text, meta FROM messages WHERE chat=? ORDER BY seq',
                                        (chat_id,)).fetchall()
        return {'id': row[0], 'title': row[1], 'workspace': row[2],
                'messages': [{'role': m[0], 'text': m[1], 'meta': json.loads(m[2])} for m in messages]}

    def rename(self, chat_id, owner, title):
        with self._lock:
            done = self._db.execute('UPDATE chats SET title=? WHERE id=? AND owner=?', (title[:LIMIT_TITLE], chat_id, owner)).rowcount
            self._db.commit()
        return bool(done)

    def delete(self, chat_id, owner):
        with self._lock:
            done = self._db.execute('DELETE FROM chats WHERE id=? AND owner=?', (chat_id, owner)).rowcount
            self._db.commit()
        return bool(done)

    def append(self, chat_id, role, text, meta=None):
        """Callers have already checked that the chat belongs to the user."""
        with self._lock:
            count = self._db.execute('SELECT COUNT(*) FROM messages WHERE chat=?', (chat_id,)).fetchone()[0]
            if count >= LIMIT_MESSAGES:
                return False
            self._db.execute('INSERT INTO messages(chat, role, text, meta) VALUES(?,?,?,?)',
                             (chat_id, role, text, json.dumps(meta or {})))
            self._db.execute('UPDATE chats SET updated=? WHERE id=?', (time.time(), chat_id))
            self._db.commit()
        return True

    def history(self, chat_id, owner):
        """Only plain drafts return to the model; blocked notices and stopped text do not."""
        chat = self.get(chat_id, owner)
        if chat is None:
            return ()
        return tuple((m['role'], m['text']) for m in chat['messages']
                     if m['role'] == 'user' or m['meta'].get('status') == 'draft')
