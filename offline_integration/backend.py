"""In-process test transport. No listener, provider, ingestion or private viewing."""

import json
import threading
from dataclasses import asdict

from boundary import unique_object
from knowledge_preflight import RequestV1, identity

from moriq.knowledge.citations import validate_references
from moriq.knowledge.registry import Registry
from moriq.knowledge.retrieval import retrieve
from offline_integration.contracts import (
    OfflineAdapter, PublicResult, Rejected, RequestEnvelope, SourceReference, envelope, identifier, require,
)


def nonfinite(_):
    raise ValueError('Invalid JSON')


def decode(payload):
    require(type(payload) is bytes and len(payload) <= 32768)
    value = json.loads(payload.decode('utf-8'), object_pairs_hook=unique_object, parse_constant=nonfinite)
    require(type(value) is dict)
    require(type(value.get('version')) is int and value['version'] == 1, 'unsupported_version')
    require(value.get('op') in ('start', 'status', 'cancel'))
    keys = {'version', 'op', 'request_id'}
    if value['op'] == 'start':
        keys |= {'request', 'sources'}
        require(keys <= value.keys() <= keys | {'generation'})
    else:
        require(value.keys() == keys)
    require(identifier(value['request_id']))
    return value


def request(value, context):
    require(type(value['request']) is dict)
    require(type(value['sources']) is list and len(value['sources']) <= 16)
    refs = []
    for ref in value['sources']:
        require(type(ref) is dict and ref.keys() == {'source_id', 'document_id', 'chunk_id'})
        refs.append(SourceReference(**ref))
    return envelope(RequestEnvelope(1, value['request_id'], context.session, RequestV1(**value['request']),
                                    tuple(refs), value.get('generation', 'disabled')))


class OfflineBackend:
    """Server-owned facade; synthetic sessions wrap, never replace, 6.1A authority.

    shortcut: Volatile test tickets and single-process locks; no production identity or durable audit.
    The registry is provisioned by the trusted host using synthetic fixtures before testing.
    """

    def __init__(self, *, server_key, credentials, request_references, registry):
        if type(server_key) is not object or type(registry) is not Registry:
            raise ValueError('Invalid offline host configuration')
        self._server = server_key
        self._boundary, self._executor = object(), object()
        self._adapter = OfflineAdapter(boundary_key=self._boundary, executor_key=self._executor,
                                       credentials=credentials, request_references=request_references)
        self._registry = registry
        self._pins = dict(request_references)
        self._sessions = {}
        self._jobs = {}
        self._lock = threading.RLock()

    def issue_session(self, server_key, actor, session):
        """Host-only test identity provisioning, never a client login operation."""
        with self._lock:
            if server_key is not self._server:
                raise ValueError('Not authorized')
            context = self._adapter.bind(self._boundary, actor, session)
            ticket = object()
            self._sessions[ticket] = context
            return ticket

    def revoke_session(self, server_key, ticket):
        with self._lock:
            if server_key is not self._server:
                raise ValueError('Not authorized')
            context = self._session(ticket)
            if context is not None:
                self._adapter.revoke(self._boundary, context)
                del self._sessions[ticket]

    def _session(self, ticket):
        return self._sessions.get(ticket) if type(ticket) is object else None

    def _sources_current(self, req):
        if not req.approved_source_references:
            return True
        query = req.request
        result = retrieve(query.search_query, self._registry, scope=query.scope,
                          jurisdiction=query.jurisdiction, edition=query.edition, max_hits=query.max_hits)
        refs = [asdict(r) for r in req.approved_source_references]
        return validate_references(self._registry, result, refs).status == 'references_valid'

    def handle(self, ticket, payload) -> bytes:
        """Client surface: bounded JSON bytes and an out-of-band test session ticket."""
        with self._lock:
            context = self._session(ticket)
            if context is None:
                return PublicResult('error', 'denied').public_json()
            try:
                value = decode(payload)
                if value['op'] == 'start':
                    result = self._start(context, request(value, context))
                else:
                    result = self._control(context, value)
                return result.public_json()
            except Rejected as exc:
                return PublicResult('error', exc.code).public_json()
            except (ValueError, TypeError, UnicodeError, RecursionError):
                return PublicResult('error', 'invalid_request').public_json()
            except Exception:
                return PublicResult('error', 'unavailable').public_json()

    def _start(self, context, req):
        # Delegate ownership/duplicate denial before consulting source state for a known ID.
        if req.request_id in self._jobs:
            return self._adapter.start(context, req).result
        fingerprint = identity(asdict(req.request))
        require(fingerprint in self._pins, 'denied')
        require(req.approved_source_references == self._pins[fingerprint], 'source_reference_denied')
        require(self._sources_current(req), 'source_reference_denied')
        receipt = self._adapter.start(context, req)
        if receipt.result.status == 'accepted':
            self._jobs[req.request_id] = (req, receipt)
        return receipt.result

    def _control(self, context, value):
        result = self._adapter.status(context, value['request_id'])
        if value['op'] == 'status' or result.status == 'error':
            return result
        # Secret stays server-side; the contract still checks owner and cancellation capability.
        _, receipt = self._jobs[value['request_id']]
        return self._adapter.cancel(context, value['request_id'], receipt.cancel_authority)

    def tick(self, server_key, ticket, request_id, expected_revision) -> bytes:
        """Trusted executor only. Clients cannot inject status changes or response bodies."""
        with self._lock:
            context = self._session(ticket)
            if server_key is not self._server or context is None:
                return PublicResult('error', 'denied').public_json()
            try:
                result = self._adapter.status(context, request_id)
                if result.status == 'error':
                    return result.public_json()
                if not result.terminal:
                    req, _ = self._jobs[request_id]
                    require(self._sources_current(req), 'source_reference_denied')
                return self._adapter.advance(self._executor, request_id, expected_revision).public_json()
            except Rejected as exc:
                return PublicResult('error', exc.code).public_json()
            except Exception:
                return PublicResult('error', 'unavailable').public_json()
