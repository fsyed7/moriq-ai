"""Offline, in-memory boundary. Test credentials only; no HTTP or production identity.

The trusted Python host owns this object. Untrusted users receive only public()
JSON, never the object, callbacks, records, exception objects or reviewer methods.
"""

import datetime as dt
import hashlib
import hmac
import json
import re
import secrets
import threading
from dataclasses import asdict, dataclass, replace

from gateway import Document, Gateway, Review, digest, validate_review

# Public bytes come only from this closed catalog, not from model/gateway text.
RESPONSES = {
    status: json.dumps({'status': status, 'message': message})
    for status, message in {
        'error': 'Request could not be processed.',
        'source_gap': 'Reviewed applicable evidence is unavailable. No answer released.',
        'review_required': 'Draft withheld for authorized review. No answer released.',
        'citation_blocked': 'Draft rejected by source identifier checks.',
        'generation_failed': 'Draft generation failed. No answer released.',
        'review_failed': 'Reviewer handoff failed. No answer released.',
    }.items()
}


@dataclass(frozen=True)
class Record:
    document: Document
    question: str
    review: Review
    creator: str
    registry_id: str
    state: str = 'pending'
    version: int = 1
    successor: str = ''


@dataclass(frozen=True)
class Event:
    sequence: int
    date: dt.date
    actor: str
    action: str
    record_id: str
    version: int


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate field.')
        result[key] = value
    return result


class OfflinePrototype:
    def __init__(self, credentials, generate, *, clock=dt.date.today):
        self._credentials = {}
        for token, (identity, roles) in credentials.items():
            if type(token) is not str or not token or type(identity) is not str or not identity.strip():
                raise ValueError('Invalid test credential.')
            roles = frozenset(roles)
            if not roles <= {'author', 'reviewer'}:
                raise ValueError('Invalid test role.')
            self._credentials[token] = (identity, roles)
        self._generate = generate
        self._clock = clock
        self._key = secrets.token_bytes(32)
        self._lock = threading.RLock()
        self._records = {}
        self._events = []
        self._drafts = []

    def _auth(self, token, role):
        if type(token) is not str or token not in self._credentials:
            raise PermissionError('Not authorized.')
        identity, roles = self._credentials[token]
        if role not in roles:
            raise PermissionError('Not authorized.')
        return identity

    def _seal(self, key, record):
        if (
            type(key) is not str
            or re.fullmatch(r'[0-9a-f]{32}', key) is None
            or type(record) is not Record
            or type(getattr(record, 'registry_id', None)) is not str
            or record.registry_id != key
        ):
            raise ValueError('Record identity failure.')
        validate_review(record.review)
        payload = asdict(record)
        for name in ('reviewed_on', 'expires_on'):
            payload['review'][name] = getattr(record.review, name).isoformat()
        # Versioned canonical JSON; no fallback stringification or legacy verification.
        data = json.dumps(
            {'format': 'moriq-attestation-v2', 'record': payload},
            sort_keys=True,
            separators=(',', ':'),
            ensure_ascii=True,
            allow_nan=False,
        ).encode('utf-8')
        return hmac.new(self._key, data, hashlib.sha256).hexdigest()

    def _save(self, key, record, actor, action):
        seal = self._seal(key, record)
        event = Event(len(self._events) + 1, self._clock(), actor, action, key, record.version)
        self._records[key] = (record, seal)
        self._events.append(event)

    def _load(self, key):
        record, seal = self._records[key]
        # A valid old MAC must not roll back a recorded revocation/supersession.
        latest = max(e.version for e in self._events if e.record_id == key)
        if record.version != latest or not hmac.compare_digest(self._seal(key, record), seal):
            raise ValueError('Record integrity failure.')
        if record.state in {'pending', 'approved'} and self._clock() > record.review.expires_on:
            record = replace(record, state='expired', version=record.version + 1)
            self._save(key, record, 'lifecycle', 'expired')
        return record

    def create(
        self,
        token,
        *,
        document,
        question,
        kind='code',
        provenance='',
        applicability='',
        jurisdiction='',
        edition='',
        expires_on=None,
    ):
        actor = self._auth(token, 'author')
        if (
            type(document) is not Document
            or type(document.text) is not str
            or not document.text.strip()
            or type(question) is not str
            or not question.strip()
        ):
            raise ValueError('Exact question and text document required.')
        review = Review(
            document.id,
            digest(document.text),
            digest(question),
            kind,
            provenance,
            applicability,
            '',
            self._clock(),
            expires_on,
            jurisdiction,
            edition,
        )
        validate_review(review)
        if (
            not provenance.strip()
            or not applicability.strip()
            or expires_on < self._clock()
            or (kind in {'code', 'fictional'} and not (jurisdiction.strip() and edition.strip()))
        ):
            raise ValueError('Incomplete or expired evidence proposal.')
        with self._lock:
            key = secrets.token_hex(16)
            self._save(key, Record(document, question, review, actor, key), actor, 'created')
            return key

    def approve(self, token, key):
        actor = self._auth(token, 'reviewer')
        with self._lock:
            record = self._load(key)
            if actor == record.creator:
                raise PermissionError('Independent approval required.')
            if record.state != 'pending':
                raise ValueError('Only pending proposals can be approved.')
            review = replace(record.review, reviewer=actor, reviewed_on=self._clock())
            self._save(
                key, replace(record, review=review, state='approved', version=record.version + 1), actor, 'approved'
            )

    def revoke(self, token, key):
        actor = self._auth(token, 'reviewer')
        with self._lock:
            record = self._load(key)
            if record.state not in {'pending', 'approved'}:
                raise ValueError('Terminal state cannot be changed.')
            self._save(key, replace(record, state='revoked', version=record.version + 1), actor, 'revoked')

    def supersede(self, token, key, successor):
        actor = self._auth(token, 'reviewer')
        with self._lock:
            old, new = self._load(key), self._load(successor)
            if (
                key == successor
                or old.state != 'approved'
                or new.state != 'approved'
                or (old.document.id, old.question, old.review.kind, old.review.jurisdiction)
                != (new.document.id, new.question, new.review.kind, new.review.jurisdiction)
            ):
                raise ValueError('Approved replacement with same source and scope required.')
            self._save(
                key, replace(old, state='superseded', successor=successor, version=old.version + 1), actor, 'superseded'
            )

    def audit(self, token):
        self._auth(token, 'reviewer')
        with self._lock:
            return tuple(self._events)

    def inspect(self, token, key):
        """Reviewer can inspect exact proposal before independently approving it."""
        actor = self._auth(token, 'reviewer')
        with self._lock:
            record = self._load(key)
            self._events.append(Event(len(self._events) + 1, self._clock(), actor, 'inspected', key, record.version))
            return record

    def _current(self, snapshot):
        return all(self._load(key) == record and record.state == 'approved' for key, record in snapshot)

    def public(self, payload):
        """Only exported public operation; fixed JSON bytes on every normal/error path."""
        try:
            if type(payload) is not str or len(payload) > 65536:
                raise ValueError('Invalid request.')
            request = json.loads(payload, object_pairs_hook=unique_object)
            if (
                type(request) is not dict
                or not {'question'} <= request.keys()
                or not request.keys() <= {'question', 'attestation_ids'}
                or type(request['question']) is not str
                or not request['question'].strip()
            ):
                raise ValueError('Invalid request schema.')
            ids = request.get('attestation_ids', [])
            if (
                type(ids) is not list
                or len(ids) > 16
                or any(type(key) is not str for key in ids)
                or len(ids) != len(set(ids))
            ):
                raise ValueError('Invalid record references.')
            with self._lock:
                snapshot = tuple((key, self._load(key)) for key in ids)
                if not self._current(snapshot):
                    return RESPONSES['source_gap']
                reviews = [record.review for _, record in snapshot]
                documents = [record.document for _, record in snapshot]
            held = []
            result = Gateway(reviews, review_sink=held.append).respond(
                request['question'], documents, generate=self._generate
            )
            with self._lock:
                # Generation runs outside the lock; stale evidence can never enter the reviewer store.
                if not self._current(snapshot):
                    return RESPONSES['source_gap']
                if result.status == 'review_required' and held:
                    self._drafts.append((snapshot, held[0]))
            return RESPONSES.get(result.status, RESPONSES['error'])
        except Exception:
            # Never serialize exception text, request content or internal objects.
            return RESPONSES['error']

    def view(self, token):
        actor = self._auth(token, 'reviewer')
        with self._lock:
            current = [(snapshot, draft) for snapshot, draft in self._drafts if self._current(snapshot)]
            result = json.dumps([asdict(draft) for _, draft in current])
            self._drafts = current
            self._events.append(Event(len(self._events) + 1, self._clock(), actor, 'drafts_viewed', '', 0))
            return result
