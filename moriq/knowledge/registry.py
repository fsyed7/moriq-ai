"""Trusted-host in-memory offline registry; never expose this object to uploads.

Host-configured credentials are test identities, not production authentication.
Approval records human review; it cannot establish the truth of that review.
"""

import datetime as dt
import hashlib
import json
import re
import threading
from dataclasses import asdict, dataclass, replace
from urllib.parse import urlsplit

MAX_BYTES = 1_000_000
CHUNK_CHARS = 1200


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fingerprint(value: dict) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode('utf-8'))


@dataclass(frozen=True)
class SourceMetadata:
    source_id: str
    title: str
    reference: str
    source_type: str
    format: str
    license: str
    usage_permission: str
    classification: str
    content_sha256: str
    revision: str
    publisher: str | None = None
    author: str | None = None
    publication_date: str | None = None
    jurisdiction: str | None = None
    code_edition: str | None = None


@dataclass(frozen=True)
class SourceRecord:
    metadata: SourceMetadata
    document_id: str
    creator: str
    version: int
    review_status: str = 'pending'
    reviewed_at: str | None = None
    reviewer: str | None = None
    lifecycle: str = 'pending'


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    document_id: str
    source_id: str
    start: int
    end: int
    content_sha256: str
    text: str
    provenance: SourceRecord


class Registry:
    """Single trusted process only; no persistence, model calls, or public adapter."""

    def __init__(self, credentials, *, local_references=()):
        self._credentials = {}
        for token, (identity, roles) in credentials.items():
            if type(token) is not str or not token or type(identity) is not str or not identity.strip():
                raise ValueError('Invalid offline credential.')
            roles = frozenset(roles)
            if not roles <= {'author', 'reviewer'}:
                raise ValueError('Invalid role.')
            self._credentials[token] = (identity, roles)
        self._local_references = frozenset(local_references)
        if any(
            type(ref) is not str or not re.fullmatch(r'local:[A-Za-z0-9][A-Za-z0-9._-]{0,150}', ref)
            for ref in self._local_references
        ):
            raise ValueError('Local references must be opaque host-approved names.')
        # shortcut: State is process-local; add protected durable lifecycle storage before real use.
        self._records = {}
        self._chunks = {}
        self._lock = threading.RLock()

    def _auth(self, token, role):
        if type(token) is not str or token not in self._credentials:
            raise PermissionError('Not authorized.')
        actor, roles = self._credentials[token]
        if role not in roles:
            raise PermissionError('Not authorized.')
        return actor

    def _validate(self, metadata):
        if type(metadata) is not SourceMetadata:
            raise ValueError('Structured source metadata required.')
        optional = {'publisher', 'author', 'publication_date', 'jurisdiction', 'code_edition'}
        for name, value in asdict(metadata).items():
            if name in optional and value is None:
                continue
            if type(value) is not str or not value.strip() or len(value) > 2048 or any(ord(c) < 32 for c in value):
                raise ValueError('Malformed source metadata.')
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:-]{0,79}', metadata.source_id):
            raise ValueError('Invalid source ID.')
        if not re.fullmatch(r'[0-9a-f]{64}', metadata.content_sha256):
            raise ValueError('Canonical content SHA-256 required.')
        self._validate_policy(metadata)

    def _validate_policy(self, metadata):
        if metadata.publication_date is not None:
            if dt.date.fromisoformat(metadata.publication_date).isoformat() != metadata.publication_date:
                raise ValueError('Canonical publication date required.')
        if metadata.source_type not in {'educational', 'guidance', 'code'} or metadata.format not in {
            'text',
            'markdown',
        }:
            raise ValueError('Unsupported document type or format.')
        if metadata.source_type == 'code' and not (metadata.jurisdiction and metadata.code_edition):
            raise ValueError('Code jurisdiction and edition required.')
        if metadata.classification != 'public':
            raise ValueError('Private or internal material prohibited.')
        if metadata.license.strip().casefold() in {'unknown', 'unspecified', 'none', 'n/a'}:
            raise ValueError('Known license required.')
        if metadata.usage_permission != 'public_redistribution':
            raise ValueError('Explicit public redistribution permission required.')
        ref = metadata.reference
        if ref in self._local_references:
            return
        url = urlsplit(ref)
        if (
            url.scheme != 'https'
            or not url.hostname
            or url.username is not None
            or url.password is not None
            or '\\' in ref
            or any(c.isspace() for c in ref)
        ):
            raise ValueError('HTTPS provenance or approved local reference required.')
        _ = url.port  # Validate port syntax without contacting the URL.

    def propose(self, token, metadata: SourceMetadata) -> SourceRecord:
        actor = self._auth(token, 'author')
        self._validate(metadata)
        with self._lock:
            old = self._records.get(metadata.source_id)
            version = old.version + 1 if old else 1
            document_id = fingerprint({'metadata': asdict(metadata), 'version': version})
            record = SourceRecord(metadata, document_id, actor, version)
            self._records[metadata.source_id] = record
            self._chunks.pop(metadata.source_id, None)
            return record

    def inspect(self, token, source_id) -> SourceRecord:
        self._auth(token, 'reviewer')
        with self._lock:
            return self._records[source_id]

    def approve(self, token, source_id, document_id) -> None:
        """Reviewer independently checks the exact proposal and original bytes."""
        actor = self._auth(token, 'reviewer')
        with self._lock:
            record = self._records[source_id]
            if actor == record.creator:
                raise PermissionError('Independent reviewer required.')
            if record.lifecycle != 'pending' or record.document_id != document_id:
                raise ValueError('Current pending document required.')
            self._records[source_id] = replace(
                record,
                review_status='approved',
                lifecycle='active',
                reviewer=actor,
                reviewed_at=dt.datetime.now(dt.UTC).isoformat(),
            )

    def withdraw(self, token, source_id, *, state='revoked') -> None:
        self._auth(token, 'reviewer')
        if state not in {'revoked', 'retired', 'superseded'}:
            raise ValueError('Invalid terminal lifecycle state.')
        with self._lock:
            record = self._records[source_id]
            if record.lifecycle not in {'pending', 'active'}:
                raise ValueError('Already withdrawn.')
            self._records[source_id] = replace(record, lifecycle=state, review_status='withdrawn')
            self._chunks.pop(source_id, None)

    def ingest(self, token, source_id, content: bytes) -> tuple[Chunk, ...]:
        self._auth(token, 'author')
        with self._lock:
            record = self._records[source_id]
            if record.lifecycle != 'active' or record.review_status != 'approved':
                raise ValueError('Approved active source required.')
            if type(content) is not bytes or not 0 < len(content) <= MAX_BYTES:
                raise ValueError('Bounded document bytes required.')
            if sha256(content) != record.metadata.content_sha256:
                raise ValueError('Content changed; fresh review required.')
            text = content.decode('utf-8', errors='strict')
            if not text.strip() or any(ord(c) < 32 and c not in '\r\n\t' for c in text):
                raise ValueError('Nonempty UTF-8 text required.')
            chunks = []
            for start in range(0, len(text), CHUNK_CHARS):
                end = min(start + CHUNK_CHARS, len(text))
                body = text[start:end]
                digest = sha256(body.encode('utf-8'))
                chunk_id = fingerprint(
                    {'document_id': record.document_id, 'start': start, 'end': end, 'sha256': digest}
                )
                chunks.append(Chunk(chunk_id, record.document_id, source_id, start, end, digest, body, record))
            self._chunks[source_id] = tuple(chunks)
            return tuple(chunks)

    def chunks(self) -> tuple[Chunk, ...]:
        """Current approved public passages, never pending bodies."""
        with self._lock:
            return tuple(
                chunk
                for key in sorted(self._chunks)
                for chunk in self._chunks[key]
                if chunk.provenance == self._records[key] and self._records[key].lifecycle == 'active'
            )


def task3_attestation_adapter(*, registry: Registry, source_id: str, question: str):
    """Reserved narrow boundary; ingestion approval is not question applicability."""
    raise PermissionError('Task 3 adapter disabled: independent question-bound attestation required.')
