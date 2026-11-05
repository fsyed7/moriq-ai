"""Accounts, passwords and sign-in sessions. Standard library only.

Passwords are stored as salted scrypt hashes and session tokens only as SHA-256 hashes, so a copy
of the database does not reveal either. The activity log records account events, never chat text.
"""

import base64
import hashlib
import hmac
import re
import secrets
import threading
import time
import uuid

USERNAME = re.compile(r'[a-z0-9][a-z0-9._-]{1,39}')
SESSION_SECONDS = 14 * 24 * 3600
MIN_PASSWORD, MAX_PASSWORD = 10, 256
MAX_FAILURES, FAILURE_WINDOW = 8, 15 * 60
MAX_CLIENT_FAILURES = 40
COMMON = frozenset({'password123', 'password1234', '1234567890', '12345678910', 'qwertyuiop', 'moriqmoriq', 'architecture',
                    'administrator', 'letmein1234', 'welcome1234', 'iloveyou12', 'passwordpassword'})
_N, _R, _P = 2 ** 15, 8, 1


class AccountError(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def _scrypt(password, salt, n=_N, r=_R, p=_P):
    return hashlib.scrypt(password.encode('utf-8'), salt=salt, n=n, r=r, p=p, maxmem=128 * 1024 * 1024, dklen=32)


def hash_password(password):
    salt = secrets.token_bytes(16)
    encode = lambda raw: base64.b64encode(raw).decode('ascii')
    return f'scrypt${_N}${_R}${_P}${encode(salt)}${encode(_scrypt(password, salt))}'


def verify_password(password, stored):
    try:
        _, n, r, p, salt, digest = stored.split('$')
        expected = base64.b64decode(digest)
        return hmac.compare_digest(_scrypt(password, base64.b64decode(salt), int(n), int(r), int(p)), expected)
    except (ValueError, TypeError):
        return False


_DUMMY = hash_password(secrets.token_urlsafe(16))  # Keeps unknown usernames as slow as real ones.


def check_password(password, username=''):
    if type(password) is not str or not MIN_PASSWORD <= len(password) <= MAX_PASSWORD:
        raise AccountError('weak_password')
    lowered = password.casefold()
    if lowered in COMMON or (username and username.casefold() in lowered) or len(set(lowered)) < 4:
        raise AccountError('weak_password')


def _token_hash(token):
    return hashlib.sha256(token.encode('ascii', 'ignore')).hexdigest()


class Accounts:
    def __init__(self, store, clock=time.time):
        self._db, self._lock, self._clock = store._db, store._lock, clock
        self._store = store
        self._failures = {}
        self._failure_lock = threading.Lock()
        with self._lock:
            self._db.executescript(
                '''CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, username TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
                     password TEXT NOT NULL, role TEXT NOT NULL, active INTEGER NOT NULL, must_change INTEGER NOT NULL,
                     created REAL NOT NULL);
                   CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY,
                     user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE, expires REAL NOT NULL);
                   CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY AUTOINCREMENT, at REAL NOT NULL, actor TEXT,
                     action TEXT NOT NULL, target TEXT);'''
            )
            self._db.commit()

    # Activity log
    def _event(self, actor, action, target=None):
        self._db.execute('INSERT INTO events(at, actor, action, target) VALUES(?,?,?,?)', (self._clock(), actor, action, target))

    def activity(self, limit=100):
        with self._lock:
            rows = self._db.execute('SELECT at, actor, action, target FROM events ORDER BY seq DESC LIMIT ?', (limit,)).fetchall()
        return [{'at': r[0], 'actor': r[1], 'action': r[2], 'target': r[3]} for r in rows]

    # Users
    def needs_setup(self):
        with self._lock:
            return self._db.execute('SELECT COUNT(*) FROM users').fetchone()[0] == 0

    @staticmethod
    def _public(row):
        return {'id': row[0], 'username': row[1], 'name': row[2], 'role': row[3], 'active': bool(row[4]), 'must_change': bool(row[5])}

    def list_users(self):
        with self._lock:
            rows = self._db.execute('SELECT id, username, name, role, active, must_change FROM users ORDER BY username').fetchall()
        return [self._public(r) for r in rows]

    def _get(self, user_id):
        row = self._db.execute('SELECT id, username, name, role, active, must_change FROM users WHERE id=?', (user_id,)).fetchone()
        return self._public(row) if row else None

    def create_user(self, username, name, password, role='member', must_change=False, actor=None):
        username = username.strip().lower() if type(username) is str else ''
        name = name.strip()[:60] if type(name) is str else ''
        if not USERNAME.fullmatch(username):
            raise AccountError('invalid_username')
        if not name:
            raise AccountError('invalid_name')
        if role not in ('admin', 'member'):
            raise AccountError('invalid_role')
        check_password(password, username)
        hashed = hash_password(password)
        with self._lock:
            if self._db.execute('SELECT 1 FROM users WHERE username=?', (username,)).fetchone():
                raise AccountError('username_taken')
            user_id = uuid.uuid4().hex
            first = self._db.execute('SELECT COUNT(*) FROM users').fetchone()[0] == 0
            self._db.execute('INSERT INTO users VALUES(?,?,?,?,?,?,?,?)',
                             (user_id, username, name, hashed, role, 1, int(must_change), self._clock()))
            if first:  # Chats from before accounts existed belong to the first admin.
                self._db.execute('UPDATE chats SET owner=? WHERE owner IS NULL', (user_id,))
            self._event(actor, 'user_created', username)
            self._db.commit()
            return self._get(user_id)

    def set_active(self, actor, user_id, active):
        with self._lock:
            user = self._get(user_id)
            if user is None:
                raise AccountError('not_found')
            if not active:
                admins = self._db.execute('SELECT COUNT(*) FROM users WHERE role=? AND active=1', ('admin',)).fetchone()[0]
                if user['id'] == actor['id']:
                    raise AccountError('cannot_disable_self')
                if user['role'] == 'admin' and user['active'] and admins <= 1:
                    raise AccountError('last_admin')
                self._db.execute('DELETE FROM sessions WHERE user_id=?', (user_id,))
            self._db.execute('UPDATE users SET active=? WHERE id=?', (int(active), user_id))
            self._event(actor['username'], 'user_enabled' if active else 'user_disabled', user['username'])
            self._db.commit()
            return self._get(user_id)

    def reset_password(self, actor_name, user_id):
        temporary = secrets.token_urlsafe(12)
        hashed = hash_password(temporary)
        with self._lock:
            user = self._get(user_id)
            if user is None:
                raise AccountError('not_found')
            self._db.execute('UPDATE users SET password=?, must_change=1 WHERE id=?', (hashed, user_id))
            self._db.execute('DELETE FROM sessions WHERE user_id=?', (user_id,))
            self._event(actor_name, 'password_reset', user['username'])
            self._db.commit()
        return temporary

    def change_password(self, user, current, new, keep_token=None):
        with self._lock:
            row = self._db.execute('SELECT password FROM users WHERE id=?', (user['id'],)).fetchone()
        if row is None or type(current) is not str or len(current) > MAX_PASSWORD or not verify_password(current, row[0]):
            raise AccountError('wrong_password')
        check_password(new, user['username'])
        if new == current:
            raise AccountError('weak_password')
        hashed = hash_password(new)
        with self._lock:
            self._db.execute('UPDATE users SET password=?, must_change=0 WHERE id=?', (hashed, user['id']))
            # Other devices must sign in again after a password change.
            self._db.execute('DELETE FROM sessions WHERE user_id=? AND token_hash<>?', (user['id'], _token_hash(keep_token or '')))
            self._event(user['username'], 'password_changed', user['username'])
            self._db.commit()

    # Password-guessing limits
    def _recent(self, key, now):
        attempts = [at for at in self._failures.get(key, ()) if now - at < FAILURE_WINDOW]
        if attempts:
            self._failures[key] = attempts
        else:
            self._failures.pop(key, None)
        return attempts

    def _blocked(self, username, client):
        now = self._clock()
        with self._failure_lock:
            return (len(self._recent(f'u:{username}', now)) >= MAX_FAILURES
                    or len(self._recent(f'c:{client}', now)) >= MAX_CLIENT_FAILURES)

    def _record_failure(self, username, client):
        now = self._clock()
        with self._failure_lock:
            if len(self._failures) > 10000:
                self._failures.clear()
            for key in (f'u:{username}', f'c:{client}'):
                self._failures.setdefault(key, []).append(now)

    def blocked_setup(self, client):
        return self._blocked('__setup__', client)

    def record_setup_failure(self, client):
        self._record_failure('__setup__', client)

    # Sessions
    def login(self, username, password, client='local'):
        username = username.strip().lower()[:40] if type(username) is str else ''
        if self._blocked(username, client):
            raise AccountError('locked')
        with self._lock:
            row = self._db.execute('SELECT id, password, active FROM users WHERE username=?', (username,)).fetchone()
        supplied = password if type(password) is str and len(password) <= MAX_PASSWORD else ''
        good = verify_password(supplied, row[1] if row else _DUMMY) and row is not None and bool(row[2])
        if not good:
            self._record_failure(username, client)
            with self._lock:
                self._event(None, 'sign_in_failed', username if row else None)
                self._db.commit()
            raise AccountError('bad_credentials')
        with self._failure_lock:
            self._failures.pop(f'u:{username}', None)
        return self.start_session(row[0], username)

    def start_session(self, user_id, username):
        token = secrets.token_urlsafe(32)
        now = self._clock()
        with self._lock:
            self._db.execute('DELETE FROM sessions WHERE expires<?', (now,))
            self._db.execute('INSERT INTO sessions VALUES(?,?,?)', (_token_hash(token), user_id, now + SESSION_SECONDS))
            self._event(username, 'signed_in', username)
            self._db.commit()
            return token, self._get(user_id)

    def session_user(self, token):
        if type(token) is not str or not token or len(token) > 128:
            return None
        with self._lock:
            row = self._db.execute(
                'SELECT u.id, u.username, u.name, u.role, u.active, u.must_change, s.expires FROM sessions s '
                'JOIN users u ON u.id=s.user_id WHERE s.token_hash=?', (_token_hash(token),)).fetchone()
        if row is None or not row[4] or row[6] < self._clock():
            return None
        return self._public(row[:6])

    def logout(self, token):
        if type(token) is not str or not token:
            return
        with self._lock:
            self._db.execute('DELETE FROM sessions WHERE token_hash=?', (_token_hash(token),))
            self._db.commit()
