"""Synthetic, owned-process applicability preflight. No execution or public API."""

import datetime as dt
import json
import re
import threading
from dataclasses import asdict, dataclass, field
from functools import wraps

from boundary import OfflinePrototype
from gateway import Document, Gateway, digest, route

from moriq.knowledge.citations import validate_references
from moriq.knowledge.registry import Registry, SnapshotIntegrity, SnapshotLimit, SourceMetadata, SourceRecord
from moriq.knowledge.retrieval import Request, _query, retrieve


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False)


def identity(value):
    return digest(canonical(value))


@dataclass(frozen=True, slots=True)
class Decision:
    status: str
    reason: str
    claim_status: str = field(default='not_assessed', init=False)
    release_allowed: bool = field(default=False, init=False)


class Denied(Exception):
    def __init__(self, reason, status='evidence_gap'):
        self.decision = Decision(status, reason)


def require(condition, reason, status='evidence_gap'):
    if not condition:
        raise Denied(reason, status)


@dataclass(frozen=True)
class RequestV1:
    question: str
    search_query: str
    jurisdiction: str
    edition: str
    max_hits: int = 5
    scope: str = 'code'
    format: str = 'moriq-knowledge-preflight-v1'


@dataclass(frozen=True)
class EvidenceEntryV1:
    alias: str
    source_id: str
    document_id: str
    chunk_id: str
    start: int
    end: int
    chunk_sha256: str
    document_sha256: str
    text: str = field(repr=False)
    provenance: SourceRecord = field(repr=False)


@dataclass(frozen=True)
class BundleV1:
    request: RequestV1 = field(repr=False)
    entries: tuple[EvidenceEntryV1, ...] = field(repr=False)
    format: str = 'moriq-knowledge-bundle-v1'

    @property
    def bundle_id(self):
        return identity(asdict(self))


def binding(bundle, entry):
    return canonical(
        {
            'format': 'moriq-knowledge-binding-v1',
            'bundle_id': bundle.bundle_id,
            'alias': entry.alias,
            'entry': asdict(entry),
        }
    )


def disabled_generation(_):
    raise RuntimeError('Preflight execution disabled')


def operation(method):
    """One owned lock and bounded call count for every operator operation."""

    @wraps(method)
    def run(self, *args, **kwargs):
        with self._lock:
            try:
                self._budget()
                return method(self, *args, **kwargs)
            except Denied as exc:
                return exc.decision
            except PermissionError:
                raise PermissionError('Not authorized.') from None
            except (SnapshotIntegrity, SnapshotLimit) as exc:
                return (
                    Decision('resource_limit', 'corpus_limit')
                    if isinstance(exc, SnapshotLimit)
                    else Decision('evidence_gap', 'integrity_failure')
                )
            except Exception:
                return Decision('evidence_gap', 'internal_failure')

    return run


class OfflineKnowledgePreflight:
    def __init__(self, credentials, *, request_hashes, source_hashes):
        # Host-only configuration, never populated from request metadata.
        roles = {'SA', 'IR', 'AP', 'QR'}
        if type(credentials) is not dict or not credentials or len(credentials) > 16:
            raise ValueError('Invalid synthetic identities')
        self._credentials = {}
        identities = {}
        for token, (actor, role) in credentials.items():
            if any(type(x) is not str or not x or len(x) > 256 for x in (token, actor, role)) or role not in roles:
                raise ValueError('Invalid synthetic identities')
            if role in identities and identities[role] != actor:
                raise ValueError('One identity per role required')
            identities[role] = actor
            self._credentials[token] = (actor, role)
        if set(identities) != roles or len(set(identities.values())) != 4:
            raise ValueError('Four independent identities required')
        self._identities = identities
        if type(request_hashes) not in (list, tuple) or len(request_hashes) > 128:
            raise ValueError('Bounded fixture requests required')
        if type(source_hashes) is not dict or len(source_hashes) > 100:
            raise ValueError('Bounded fixture sources required')
        if any(
            type(h) is not str or re.fullmatch(r'[0-9a-f]{64}', h) is None
            for h in [*request_hashes, *source_hashes.values()]
        ):
            raise ValueError('Canonical fixture hashes required')
        if any(
            type(k) is not str or re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:-]{0,79}', k) is None for k in source_hashes
        ):
            raise ValueError('Invalid fixture source ID')
        self._requests = frozenset(request_hashes)
        self._sources = dict(source_hashes)
        self._verifier = next(t for t, (_, role) in self._credentials.items() if role == 'QR')
        self._source_reviewer = next(t for t, (_, role) in self._credentials.items() if role == 'IR')
        self._registry = Registry(
            {
                t: (a, {'author' if r == 'SA' else 'reviewer'})
                for t, (a, r) in self._credentials.items()
                if r in {'SA', 'IR'}
            }
        )
        self._attestations = OfflinePrototype(
            {
                t: (a, {'author' if r == 'AP' else 'reviewer'})
                for t, (a, r) in self._credentials.items()
                if r in {'AP', 'QR'}
            },
            disabled_generation,
            clock=lambda: dt.date.today(),
        )
        self._lock = threading.RLock()
        self._flight = threading.Lock()
        self._calls = self._proposals = self._records = 0
        # shortcut: Process-local authority only; durable identity/audit needs separate review.

    def _auth(self, token, role):
        if type(token) is not str or self._credentials.get(token, (None, None))[1] != role:
            raise PermissionError('Not authorized.')

    def _budget(self):
        require(self._calls < 1024, 'input_limit', 'resource_limit')
        self._calls += 1

    def _request(self, value):
        if type(value) is dict:
            require(set(value) <= set(RequestV1.__dataclass_fields__), 'schema', 'invalid_request')
            try:
                value = RequestV1(**value)
            except TypeError:
                raise Denied('schema', 'invalid_request') from None
        require(type(value) is RequestV1, 'schema', 'invalid_request')
        require(type(value.max_hits) is int and 1 <= value.max_hits <= 16, 'schema', 'invalid_request')
        for name in ('question', 'search_query', 'jurisdiction', 'edition', 'scope', 'format'):
            text = getattr(value, name)
            require(type(text) is str and bool(text.strip()), 'schema', 'invalid_request')
            cap = 512 if name in {'question', 'search_query'} else 256
            require(len(text) <= cap, 'input_limit', 'resource_limit')
            try:
                text.encode('utf-8')
            except UnicodeError:
                raise Denied('schema', 'invalid_request') from None
        require(
            value.format == 'moriq-knowledge-preflight-v1' and value.scope in {'code', 'general', 'company', 'mixed'},
            'schema',
            'invalid_request',
        )
        require(len(canonical(asdict(value)).encode()) <= 16384, 'input_limit', 'resource_limit')
        status, _, _ = _query(
            Request(value.search_query, value.scope, value.jurisdiction, value.edition, value.max_hits)
        )
        require(status != 'resource_limit', 'input_limit', 'resource_limit')
        return value

    def _prepare(self, request):
        require(identity(asdict(request)) in self._requests, 'authorization_missing')
        require(request.scope == 'code' and route(request.question) == 'code', 'unsupported_scope')
        epoch, _ = self._registry.snapshot()
        result = retrieve(
            request.search_query,
            self._registry,
            scope=request.scope,
            jurisdiction=request.jurisdiction,
            edition=request.edition,
            max_hits=request.max_hits,
        )
        if result.status != 'passages':
            if result.status == 'resource_limit':
                raise Denied('corpus_limit', 'resource_limit')
            raise Denied('integrity_failure' if result.status == 'integrity_error' else 'no_evidence')
        refs = [
            dict(source_id=h.chunk.source_id, document_id=h.chunk.document_id, chunk_id=h.chunk.chunk_id)
            for h in result.hits
        ]
        require(validate_references(self._registry, result, refs).status == 'references_valid', 'integrity_failure')
        entries = []
        size = 0
        for i, c in enumerate(
            sorted((h.chunk for h in result.hits), key=lambda c: (c.source_id, c.document_id, c.start, c.chunk_id)), 1
        ):
            require(self._sources.get(c.source_id) == c.provenance.metadata.content_sha256, 'authorization_missing')
            size += len(c.text.encode('utf-8'))
            require(size <= 32768, 'input_limit', 'resource_limit')
            entries.append(
                EvidenceEntryV1(
                    str(i),
                    c.source_id,
                    c.document_id,
                    c.chunk_id,
                    c.start,
                    c.end,
                    c.content_sha256,
                    c.provenance.metadata.content_sha256,
                    c.text,
                    c.provenance,
                )
            )
        bundle = BundleV1(request, tuple(entries))
        require(len(canonical(asdict(bundle)).encode()) <= 65536, 'input_limit', 'resource_limit')
        require(self._registry.current(epoch), 'stale_snapshot')
        return bundle, epoch

    def _held(self, request, bundle):
        require(type(bundle) is BundleV1, 'binding_mismatch')
        fresh, _ = self._prepare(request)
        require(bundle == fresh, 'binding_mismatch')
        return fresh

    @operation
    def propose_source(self, token, metadata):
        self._auth(token, 'SA')
        require(self._proposals < 100, 'input_limit', 'resource_limit')
        require(type(metadata) is SourceMetadata, 'schema', 'invalid_request')
        require(self._sources.get(metadata.source_id) == metadata.content_sha256, 'authorization_missing')
        record = self._registry.propose(token, metadata)
        self._proposals += 1
        return record

    @operation
    def approve_source(self, token, source_id, document_id):
        self._auth(token, 'IR')
        self._registry.approve(token, source_id, document_id)

    @operation
    def ingest(self, token, source_id, content):
        self._auth(token, 'SA')
        require(type(content) is bytes, 'schema', 'invalid_request')
        require(len(content) <= 1000000, 'input_limit', 'resource_limit')
        self._registry.ingest(token, source_id, content)

    @operation
    def withdraw_source(self, token, source_id, state='revoked'):
        self._auth(token, 'IR')
        self._registry.withdraw(token, source_id, state=state)

    @operation
    def prepare(self, request):
        return self._prepare(self._request(request))[0]

    @operation
    def inspect_bundle(self, token, request, bundle):
        self._auth(token, 'QR')
        return self._held(self._request(request), bundle)

    @operation
    def inspect_attestation(self, token, key):
        self._auth(token, 'QR')
        return self._attestations.inspect(token, key)

    @operation
    def propose_applicability(self, token, request, bundle, alias, applicability, expires_on):
        self._auth(token, 'AP')
        require(self._records < 256, 'input_limit', 'resource_limit')
        request = self._request(request)
        try:
            fresh = self._held(request, bundle)
        except Denied as exc:
            if exc.decision.reason == 'no_evidence':
                raise Denied('stale_source') from None
            raise
        require(type(alias) is str and alias in {e.alias for e in fresh.entries}, 'binding_mismatch')
        require(type(applicability) is str and bool(applicability.strip()), 'schema', 'invalid_request')
        require(len(applicability) <= 2048, 'input_limit', 'resource_limit')
        require(
            type(expires_on) is dt.date and dt.date.today() <= expires_on <= dt.date.today() + dt.timedelta(days=7),
            'binding_mismatch',
        )
        entry = next(e for e in fresh.entries if e.alias == alias)
        key = self._attestations.create(
            token,
            document=Document(alias, entry.text),
            question=request.question,
            kind='fictional',
            provenance=binding(fresh, entry),
            applicability=applicability,
            jurisdiction=request.jurisdiction,
            edition=request.edition,
            expires_on=expires_on,
        )
        self._records += 1
        return key

    def _matches(self, record, bundle, entry, *, pending=False):
        review = record.review
        return (
            record.question == bundle.request.question
            and record.document == Document(entry.alias, entry.text)
            and record.creator == self._identities['AP']
            and review.source_id == entry.alias
            and review.content_sha256 == entry.chunk_sha256
            and review.question_sha256 == digest(bundle.request.question)
            and review.provenance == binding(bundle, entry)
            and review.kind == 'fictional'
            and review.jurisdiction == bundle.request.jurisdiction
            and review.edition == bundle.request.edition
            and bool(review.applicability.strip())
            and len(review.applicability) <= 2048
            and (pending or review.reviewer == self._identities['QR'])
            and review.reviewed_on <= dt.date.today() <= review.expires_on
            and review.reviewed_on <= review.expires_on <= review.reviewed_on + dt.timedelta(days=7)
        )

    @operation
    def approve_applicability(self, token, request, bundle, key):
        self._auth(token, 'QR')
        fresh = self._held(self._request(request), bundle)
        record = self._attestations.inspect(token, key)
        require(record.state == 'pending', 'stale_attestation')
        entry = next((e for e in fresh.entries if e.alias == record.document.id), None)
        require(entry is not None and self._matches(record, fresh, entry, pending=True), 'binding_mismatch')
        self._attestations.approve(token, key)

    @operation
    def revoke(self, token, key):
        self._auth(token, 'QR')
        self._attestations.revoke(token, key)

    @operation
    def supersede(self, token, key, successor):
        self._auth(token, 'QR')
        self._attestations.supersede(token, key, successor)

    def check(self, request, attestation_ids):
        try:
            require(
                type(request) in (dict, RequestV1) and type(attestation_ids) in (list, tuple),
                'schema',
                'invalid_request',
            )
            require(len(attestation_ids) <= 16, 'reference_limit', 'resource_limit')
            request = self._request(request)
            require(
                all(type(k) is str and re.fullmatch(r'[0-9a-f]{32}', k) for k in attestation_ids),
                'schema',
                'invalid_request',
            )
            require(len(set(attestation_ids)) == len(attestation_ids), 'schema', 'invalid_request')
            require(bool(attestation_ids), 'missing_applicability')
            require(self._flight.acquire(blocking=False), 'busy', 'resource_limit')
            try:
                with self._lock:
                    self._budget()
                    return self._check(request, tuple(sorted(attestation_ids)))
            finally:
                self._flight.release()
        except Denied as exc:
            return exc.decision
        except PermissionError:
            return Decision('evidence_gap', 'authorization_missing')
        except SnapshotLimit:
            return Decision('resource_limit', 'corpus_limit')
        except SnapshotIntegrity:
            return Decision('evidence_gap', 'integrity_failure')
        except Exception:
            return Decision('evidence_gap', 'internal_failure')

    def _inspect(self, key):
        try:
            return self._attestations.inspect(self._verifier, key)
        except KeyError:
            raise Denied('missing_applicability') from None
        except (ValueError, TypeError, AttributeError):
            raise Denied('integrity_failure') from None

    def _check(self, request, ids):
        today = dt.date.today()
        bundle, epoch = self._prepare(request)
        records = tuple((key, self._inspect(key)) for key in ids)
        require(all(r.state == 'approved' for _, r in records), 'stale_attestation')
        require(len(records) >= len(bundle.entries), 'missing_applicability')
        require(len(records) == len(bundle.entries), 'binding_mismatch')
        by_alias = {r.document.id: r for _, r in records}
        require(len(by_alias) == len(records), 'binding_mismatch')
        for entry in bundle.entries:
            require(entry.alias in by_alias and self._matches(by_alias[entry.alias], bundle, entry), 'binding_mismatch')
        verified = tuple(by_alias[e.alias] for e in bundle.entries)
        require(
            Gateway(tuple(r.review for r in verified), exercise=True).eligible(
                request.question, tuple(r.document for r in verified), 'code'
            ),
            'not_applicable',
        )
        require(self._registry.current(epoch) and all(self._inspect(k) == r for k, r in records), 'stale_snapshot')
        require(dt.date.today() == today, 'clock_changed')
        return Decision('evidence_ready', 'structural_only')
