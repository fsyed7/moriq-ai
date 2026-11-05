"""In-process contract exercise. No provider, retrieval, source approval or public endpoint."""

import re
import secrets
import threading
from dataclasses import asdict, dataclass, field, replace
from typing import Literal

from knowledge_preflight import RequestV1, canonical, identity
from private_draft_lifecycle import OfflinePrivateDraftLifecycle

Status = Literal['accepted', 'validating', 'failed', 'cancelled', 'error']
Code = Literal[
    'none',
    'invalid_request',
    'unsupported_version',
    'denied',
    'source_reference_denied',
    'generation_disabled',
    'duplicate_request',
    'stale_response',
    'terminal_state',
    'source_gap',
    'unavailable',
    'resource_limit',
]
TERMINAL = frozenset({'failed', 'cancelled'})


def identifier(value):
    return type(value) is str and re.fullmatch(r'[A-Za-z0-9_-]{1,64}', value) is not None


@dataclass(frozen=True, slots=True)
class SourceReference:
    source_id: str
    document_id: str
    chunk_id: str


@dataclass(frozen=True, slots=True, repr=False)
class ActorContext:
    """Only the exact object registered by the trusted boundary is a capability."""

    actor: str
    session: str


@dataclass(frozen=True, slots=True, repr=False)
class RequestEnvelope:
    version: int
    request_id: str
    session: str
    request: RequestV1
    approved_source_references: tuple[SourceReference, ...] = ()
    generation: str = 'disabled'


@dataclass(frozen=True, slots=True)
class PublicResult:
    status: Status
    code: Code
    request_id: str | None = None
    revision: int = 0
    terminal: bool = False
    version: int = field(default=1, init=False)
    claim_status: str = field(default='not_assessed', init=False)
    release_allowed: bool = field(default=False, init=False)
    sources: tuple[SourceReference, ...] = field(default=(), init=False)

    def public_json(self) -> bytes:
        return canonical(asdict(self)).encode('utf-8')


@dataclass(frozen=True, slots=True, repr=False)
class Submission:
    """Host-only receipt; serialize public_json(), never the receipt/cancel capability."""

    result: PublicResult
    cancel_authority: str | None = None

    def public_json(self) -> bytes:
        return self.result.public_json()


@dataclass(frozen=True, slots=True, repr=False)
class Pending:
    context: ActorContext
    envelope: RequestEnvelope
    lifecycle_id: str
    cancel_authority: str
    result: PublicResult


class Rejected(Exception):
    def __init__(self, code):
        self.code = code


def require(condition, code='invalid_request'):
    if not condition:
        raise Rejected(code)


def references(value):
    require(type(value) is tuple and len(value) <= 16)
    for ref in value:
        require(type(ref) is SourceReference)
        require(type(ref.source_id) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:-]{0,79}', ref.source_id))
        require(all(type(v) is str and re.fullmatch(r'[0-9a-f]{64}', v) for v in (ref.document_id, ref.chunk_id)))
    require(len(set(value)) == len(value))
    return value


def envelope(value):
    """Typed host contract, intentionally no permissive dict/JSON deserialization."""
    require(type(value) is RequestEnvelope)
    require(type(value.version) is int and value.version == 1, 'unsupported_version')
    require(identifier(value.request_id) and identifier(value.session))
    require(type(value.generation) is str and value.generation == 'disabled', 'generation_disabled')
    require(type(value.request) is RequestV1)
    req = value.request
    require(type(req.max_hits) is int and 1 <= req.max_hits <= 16)
    for key in ('question', 'search_query', 'scope', 'jurisdiction', 'edition', 'format'):
        text = getattr(req, key)
        require(
            type(text) is str
            and bool(text.strip())
            and len(text) <= (512 if key in {'question', 'search_query'} else 256)
        )
        text.encode('utf-8')
    require(req.format == 'moriq-knowledge-preflight-v1' and req.scope in {'general', 'code', 'company', 'mixed'})
    references(value.approved_source_references)
    require(len(canonical(asdict(value)).encode()) <= 16384)
    return value


class OfflineAdapter:
    """Exclusive owner. Boundary/executor keys are host objects, never client inputs.

    shortcut: Volatile synthetic context capabilities; real auth/audit/recovery is a later gate.
    Source pins are contract inputs only, never ingestion/applicability or disclosure authority.
    """

    def __init__(self, *, boundary_key, executor_key, credentials, request_references):
        if type(boundary_key) is not object or type(executor_key) is not object or boundary_key is executor_key:
            raise ValueError('Distinct host capabilities required')
        if type(request_references) is not dict or len(request_references) > 32:
            raise ValueError('Bounded offline configuration required')
        try:
            for key, refs in request_references.items():
                require(type(key) is str and re.fullmatch(r'[0-9a-f]{64}', key))
                references(refs)
        except Exception:
            raise ValueError('Invalid offline configuration') from None
        self._owner = OfflinePrivateDraftLifecycle(
            credentials, request_hashes=list(request_references), source_hashes={}, fixtures={}
        )
        self._ra = next(t for t, (_, role) in credentials.items() if role == 'RA')
        self._pins = dict(request_references)
        self._boundary, self._executor = boundary_key, executor_key
        self._contexts: list[ActorContext] = []
        self._pending: dict[str, Pending] = {}
        self._lock = threading.RLock()

    def bind(self, key, actor, session):
        """Trusted boundary only, after its own authentication; no HTTP identity claim."""
        with self._lock:
            if (
                key is not self._boundary
                or not identifier(actor)
                or not identifier(session)
                or len(self._contexts) >= 16
            ):
                raise ValueError('Context unavailable')
            context = ActorContext(actor, session)
            self._contexts.append(context)
            return context

    def revoke(self, key, context):
        with self._lock:
            if key is not self._boundary:
                raise ValueError('Context unavailable')
            self._contexts = [c for c in self._contexts if c is not context]

    def _authenticated(self, context):
        return any(c is context for c in self._contexts)

    def _owned(self, context, request_id):
        if not self._authenticated(context) or not identifier(request_id):
            return None
        row = self._pending.get(request_id)
        return row if row is not None and row.context is context else None

    def start(self, context, request) -> Submission:
        with self._lock:
            if not self._authenticated(context):
                return Submission(PublicResult('error', 'denied'))
            try:
                value = envelope(request)
                require(value.session == context.session, 'denied')
                old = self._pending.get(value.request_id)
                if old is not None:
                    require(old.context is context, 'denied')
                    raise Rejected('duplicate_request')
                require(len(self._pending) < 32, 'resource_limit')
                fingerprint = identity(asdict(value.request))
                require(fingerprint in self._pins, 'denied')
                require(value.approved_source_references == self._pins[fingerprint], 'source_reference_denied')
                cancel = secrets.token_hex(32)
                lifecycle_id = self._owner.create_request(self._ra, value.request)
                require(type(lifecycle_id) is str, 'unavailable')
                result = PublicResult('accepted', 'none', value.request_id, 1)
                self._pending[value.request_id] = Pending(context, value, lifecycle_id, cancel, result)
                return Submission(result, cancel)
            except Rejected as exc:
                return Submission(PublicResult('error', exc.code))
            except (TypeError, ValueError, UnicodeError):
                return Submission(PublicResult('error', 'invalid_request'))
            except Exception:
                return Submission(PublicResult('error', 'unavailable'))

    def status(self, context, request_id) -> PublicResult:
        with self._lock:
            row = self._owned(context, request_id)
            return row.result if row else PublicResult('error', 'denied')

    def _transition(self, row, status, code):
        result = PublicResult(status, code, row.result.request_id, row.result.revision + 1, status in TERMINAL)
        self._pending[row.result.request_id] = replace(row, result=result)
        return result

    def cancel(self, context, request_id, cancel_authority) -> PublicResult:
        with self._lock:
            row = self._owned(context, request_id)
            if (
                row is None
                or type(cancel_authority) is not str
                or len(cancel_authority) != 64
                or not cancel_authority.isascii()
                or not secrets.compare_digest(cancel_authority, row.cancel_authority)
            ):
                return PublicResult('error', 'denied')
            if row.result.status == 'cancelled':
                return row.result
            if row.result.terminal:
                return PublicResult('error', 'terminal_state')
            return self._transition(row, 'cancelled', 'none')

    def advance(self, key, request_id, expected_revision) -> PublicResult:
        """Trusted executor tick, not a client-selected transition or response body."""
        with self._lock:
            if key is not self._executor or not identifier(request_id):
                return PublicResult('error', 'denied')
            row = self._pending.get(request_id)
            if row is None or not self._authenticated(row.context):
                return PublicResult('error', 'denied')
            if type(expected_revision) is not int or expected_revision != row.result.revision:
                return PublicResult('error', 'stale_response')
            if row.result.terminal:
                return PublicResult('error', 'terminal_state')
            if row.result.status == 'accepted':
                return self._transition(row, 'validating', 'none')
            code = 'generation_disabled' if row.envelope.approved_source_references else 'source_gap'
            return self._transition(row, 'failed', code)
