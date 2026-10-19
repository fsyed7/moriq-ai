"""Trusted-process synthetic fixture lifecycle. No generator, transport or persistence."""

import datetime as dt
import secrets
import threading
from dataclasses import asdict, dataclass, replace
from functools import wraps

from gateway import Draft, citations_valid, digest
from knowledge_preflight import BundleV1, Decision, OfflineKnowledgePreflight, RequestV1, canonical, identity

DENIED = b'{"status":"denied","release_allowed":false}'
WITHHELD = b'{"status":"withheld","release_allowed":false}'


class Denial(Exception):
    pass


def require(value):
    if not value:
        raise Denial


@dataclass(frozen=True, repr=False)
class RequestContext:
    request_id: str
    version: int
    request: RequestV1
    content_hash: str


class RequestContextAuthority:
    """Internal owner state: access only while the lifecycle owner's lock is held."""

    def __init__(self):
        self.available = True
        self.records = {}

    def current(self, key):
        require(self.available and type(key) is str and len(key) == 32)
        record = self.records.get(key)
        require(type(record) is RequestContext and record.request_id == key)
        require(type(record.version) is int and record.version > 0)
        require(record.content_hash == identity(asdict(record.request)))
        return record


@dataclass(frozen=True, repr=False)
class Fixture:
    request_hash: str
    sources: tuple[str, ...]
    text: str
    aliases: tuple[str, ...]
    sha256: str


@dataclass(frozen=True, repr=False)
class Lease:
    document_id: str
    source_hash: str
    reviewer: str
    version: int
    deadline: dt.datetime


@dataclass(frozen=True, repr=False)
class Grant:
    subject: str
    version: int
    deadline: dt.datetime
    active: bool = True


@dataclass(frozen=True, repr=False)
class Held:
    context: RequestContext
    bundle: BundleV1
    ids: tuple[str, ...]
    versions: tuple[int, ...]
    leases: tuple[tuple[str, Lease], ...]
    fixture_id: str
    deadline: dt.datetime
    generation: int
    state: str = 'reservation'
    text: str = ''


@dataclass(frozen=True, repr=False)
class Permit:
    draft_id: str
    context: RequestContext
    subject: str
    grant_version: int
    generation: int
    deadline: dt.datetime


@dataclass(frozen=True)
class AuditEvent:
    sequence: int
    session: str
    draft_id: str
    action: str
    result: str


def operation(*, reader=False):
    def decorate(method):
        @wraps(method)
        def run(self, *args, **kwargs):
            admitted = False
            waiting = False
            try:
                with self._admission:
                    if reader:
                        require(not self._reading and not self._waiting)
                        self._reading = admitted = True
                    else:
                        self._waiting += 1
                        waiting = True
                with self._lock:
                    if waiting:
                        with self._admission:
                            self._waiting -= 1
                        waiting = False
                    require(self._healthy and self._operations < 256)
                    self._operations += 1
                    self._time()
                    return method(self, *args, **kwargs)
            except Denial:
                return DENIED
            except Exception:
                # Never forward exception objects, arguments or tracebacks to callers.
                with self._lock:
                    self._healthy = False
                return DENIED
            finally:
                with self._admission:
                    if admitted:
                        self._reading = False
                    if waiting:
                        self._waiting -= 1

        return run

    return decorate


class OfflinePrivateDraftLifecycle:
    @staticmethod
    def _roles(credentials):
        roles = {'SA', 'IR', 'AP', 'QR', 'PV', 'RA'}
        if type(credentials) is not dict or not 6 <= len(credentials) <= 16:
            raise ValueError('Invalid synthetic configuration')
        actors = {}
        for token, pair in credentials.items():
            if type(pair) is not tuple or len(pair) != 2:
                raise ValueError('Invalid synthetic configuration')
            actor, role = pair
            if any(type(x) is not str or not x or len(x) > 256 for x in (token, actor, role)) or role not in roles:
                raise ValueError('Invalid synthetic configuration')
            if role in actors and actors[role] != actor:
                raise ValueError('Invalid synthetic configuration')
            actors[role] = actor
        if set(actors) != roles or len(set(actors.values())) != 6:
            raise ValueError('Independent synthetic roles required')
        return actors

    def __init__(self, credentials, *, request_hashes, source_hashes, fixtures):
        actors = self._roles(credentials)
        if type(fixtures) is not dict or len(fixtures) > 32:
            raise ValueError('Bounded fixture catalog required')
        for key, f in fixtures.items():
            if type(key) is not str or not key or len(key) > 80 or type(f) is not Fixture:
                raise ValueError('Invalid synthetic fixture')
            if (
                type(f.text) is not str
                or not f.text.startswith('SYNTHETIC TEST ONLY: ')
                or len(f.text.encode()) > 65536
                or f.sha256 != digest(f.text)
                or type(f.sources) is not tuple
                or not 1 <= len(f.sources) <= 16
                or any(type(s) is not str or s not in source_hashes for s in f.sources)
                or len(set(f.sources)) != len(f.sources)
                or f.request_hash not in request_hashes
                or not citations_valid(Draft(f.text, f.aliases), {str(i) for i in range(1, 17)})
            ):
                raise ValueError('Invalid synthetic fixture')
        self._credentials = dict(credentials)
        self._actors = actors
        self._preflight = OfflineKnowledgePreflight(
            {t: pair for t, pair in credentials.items() if pair[1] in {'SA', 'IR', 'AP', 'QR'}},
            request_hashes=request_hashes,
            source_hashes=source_hashes,
        )
        self._qr = next(t for t, (_, role) in credentials.items() if role == 'QR')
        self._requests = frozenset(request_hashes)
        self._fixtures = dict(fixtures)
        self._authority = RequestContextAuthority()
        self._contexts = {}  # Independently held version/hash ledger detects snapshot substitution.
        self._lock = threading.RLock()
        self._admission = threading.Lock()
        self._reading = False
        self._waiting = 0
        self._healthy = self._auth_available = self._audit_available = True
        self._session = secrets.token_hex(16)
        self._operations = self._generation = self._permit_count = 0
        self._leases = {}
        self._grants = {}
        self._drafts = {}
        self._permits = {}
        self._events = []
        self._last_time = None
        # shortcut: Host-owned volatile authority; production needs durable transactions and identity.

    @staticmethod
    def public_result():
        return WITHHELD

    def _auth(self, token, role):
        require(self._auth_available and type(token) is str and len(token) <= 256)
        actor, actual = self._credentials.get(token, ('', ''))
        require(actual == role)
        return actor

    def _time(self, initial=None):
        try:
            now = dt.datetime.now(dt.UTC)
            require(now.tzinfo == dt.UTC and now.date() == dt.date.today())
            require(self._last_time is None or now >= self._last_time)
            require(initial is None or now.date() == initial.date())
            self._last_time = now
            return now
        except Exception:
            self._healthy = False
            raise Denial from None

    def _audit(self, action, key=''):
        # Append only a proposal here: a throwing append must not record a successful copy.
        needed = 2 if action == 'private_copy' else 1
        if not self._audit_available or len(self._events) + needed > 2048:
            self._healthy = False
            raise Denial
        self._events.append(AuditEvent(len(self._events) + 1, self._session, key, action, 'intent'))

    def _changed(self):
        self._generation += 1
        self._permits.clear()
        for key, held in tuple(self._drafts.items()):
            if held.state == 'reservation':
                self._drafts[key] = replace(held, state='invalidated', text='')

    def _context(self, key):
        context = self._authority.current(key)
        require(self._contexts.get(key) == (context.version, context.content_hash))
        return context

    def _request(self, request):
        require(type(request) is RequestV1)
        for name in RequestV1.__dataclass_fields__:
            value = getattr(request, name)
            if name == 'max_hits':
                require(type(value) is int and 1 <= value <= 16)
            else:
                require(type(value) is str and len(value) <= (512 if name in {'question', 'search_query'} else 256))
                value.encode()
        require(len(canonical(asdict(request)).encode()) <= 16384)
        fingerprint = identity(asdict(request))
        require(fingerprint in self._requests)
        return fingerprint

    @operation()
    def create_request(self, token, request):
        self._auth(token, 'RA')
        require(self._authority.available and len(self._contexts) < 32)
        fingerprint = self._request(request)
        self._audit('request_create')
        key = secrets.token_hex(16)
        self._authority.records[key] = RequestContext(key, 1, request, fingerprint)
        self._contexts[key] = (1, fingerprint)
        return key

    @operation()
    def update_request(self, token, key, request):
        self._auth(token, 'RA')
        old = self._context(key)
        fingerprint = self._request(request)
        if old.content_hash == fingerprint:
            return key
        self._audit('request_update')
        self._authority.records[key] = RequestContext(key, old.version + 1, request, fingerprint)
        self._contexts[key] = (old.version + 1, fingerprint)
        for draft_id, held in tuple(self._drafts.items()):
            if held.context.request_id == key:
                self._drafts[draft_id] = replace(held, state='invalidated', text='')
        self._permits = {p: v for p, v in self._permits.items() if v.context.request_id != key}
        return key

    def _evidence(self, action, token, role, *args):
        self._auth(token, role)
        self._audit(action)
        result = getattr(self._preflight, action)(token, *args)
        if type(result) is Decision:
            if action in {'withdraw_source', 'revoke', 'supersede'}:
                self._healthy = False
            raise Denial
        self._changed()
        return result

    @operation()
    def propose_source(self, token, metadata):
        return self._evidence('propose_source', token, 'SA', metadata)

    @operation()
    def approve_source(self, token, source_id, document_id):
        return self._evidence('approve_source', token, 'IR', source_id, document_id)

    @operation()
    def ingest(self, token, source_id, content):
        return self._evidence('ingest', token, 'SA', source_id, content)

    @operation()
    def withdraw_source(self, token, source_id, state='revoked'):
        return self._evidence('withdraw_source', token, 'IR', source_id, state)

    @operation(reader=True)
    def prepare(self, token, request_id):
        self._auth(token, 'QR')
        result = self._preflight.prepare(self._context(request_id).request)
        require(type(result) is BundleV1)
        return result

    @operation()
    def propose_applicability(self, token, request_id, bundle, alias, applicability, expires_on):
        self._auth(token, 'AP')
        return self._evidence(
            'propose_applicability',
            token,
            'AP',
            self._context(request_id).request,
            bundle,
            alias,
            applicability,
            expires_on,
        )

    @operation()
    def approve_applicability(self, token, request_id, bundle, key):
        self._auth(token, 'QR')
        return self._evidence('approve_applicability', token, 'QR', self._context(request_id).request, bundle, key)

    @operation()
    def revoke(self, token, key):
        return self._evidence('revoke', token, 'QR', key)

    @operation()
    def supersede(self, token, key, successor):
        return self._evidence('supersede', token, 'QR', key, successor)

    @operation()
    def lease_source(self, token, request_id, source_id, deadline):
        actor = self._auth(token, 'IR')
        now = self._time()
        require(type(deadline) is dt.datetime and now < deadline <= now + dt.timedelta(days=7))
        bundle = self._preflight.prepare(self._context(request_id).request)
        require(type(bundle) is BundleV1)
        entry = next((e for e in bundle.entries if e.source_id == source_id), None)
        require(entry is not None)
        self._audit('lease')
        old = self._leases.get(source_id)
        self._leases[source_id] = Lease(
            entry.document_id, entry.document_sha256, actor, 1 if old is None else old.version + 1, deadline
        )
        self._changed()

    @operation()
    def grant_reviewer(self, draft_id, deadline):
        """Trusted bootstrap host only, never a credential-bearing reviewer endpoint."""
        now = self._time()
        require(type(draft_id) is str and draft_id in self._drafts)
        require(type(deadline) is dt.datetime and now < deadline <= now + dt.timedelta(days=7))
        self._audit('grant')
        old = self._grants.get(draft_id)
        self._grants[draft_id] = Grant(self._actors['PV'], 1 if old is None else old.version + 1, deadline)
        self._changed()

    @operation()
    def revoke_reviewer(self, draft_id):
        require(type(draft_id) is str and draft_id in self._grants)
        self._audit('grant_revoke')
        old = self._grants[draft_id]
        self._grants[draft_id] = replace(old, active=False, version=old.version + 1)
        self._changed()

    def _binding(self, context, ids):
        require(type(ids) in (tuple, list) and 0 < len(ids) <= 16)
        result = self._preflight.check(context.request, ids)
        require(result == Decision('evidence_ready', 'structural_only'))
        bundle = self._preflight.prepare(context.request)
        require(type(bundle) is BundleV1 and len(canonical(asdict(bundle)).encode()) <= 65536)
        versions = []
        for key in sorted(ids):
            record = self._preflight.inspect_attestation(self._qr, key)
            require(type(record) is not Decision and record.state == 'approved')
            versions.append(record.version)
        leases = []
        now = self._time()
        for entry in bundle.entries:
            lease = self._leases.get(entry.source_id)
            require(type(lease) is Lease and now < lease.deadline)
            require(lease.document_id == entry.document_id and lease.source_hash == entry.document_sha256)
            leases.append((entry.source_id, lease))
        return bundle, tuple(versions), tuple(leases)

    def _valid(self, key, held):
        try:
            require(held.state in {'reservation', 'held'} and self._time() < held.deadline)
            require(self._context(held.context.request_id) == held.context)
            bundle, versions, leases = self._binding(held.context, held.ids)
            require((bundle, versions, leases) == (held.bundle, held.versions, held.leases))
            fixture = self._fixtures[held.fixture_id]
            require(fixture.request_hash == held.context.content_hash)
            require(tuple(sorted({e.source_id for e in bundle.entries})) == tuple(sorted(fixture.sources)))
            require(fixture.sha256 == digest(fixture.text) and len(fixture.text.encode()) <= 65536)
            require(citations_valid(Draft(fixture.text, fixture.aliases), {e.alias for e in bundle.entries}))
            if held.state == 'held':
                require(held.text == fixture.text)
            return fixture
        except Exception:
            if key in self._drafts:
                self._drafts[key] = replace(held, state='invalidated', text='')
            raise Denial from None

    @operation(reader=True)
    def begin_fixture(self, fixture_id, request_id, ids):
        require(type(ids) in (list, tuple) and len(ids) <= 16)
        require(type(fixture_id) is str and fixture_id in self._fixtures and len(self._drafts) < 32)
        start = self._time()
        context = self._context(request_id)
        bundle, versions, leases = self._binding(context, ids)
        deadline = min(start + dt.timedelta(seconds=300), *(lease.deadline for _, lease in leases))
        held = Held(context, bundle, tuple(sorted(ids)), versions, leases, fixture_id, deadline, self._generation)
        key = secrets.token_hex(16)
        self._valid(key, held)
        self._time(start)
        self._audit('reserve')
        self._drafts[key] = held
        return key

    @operation(reader=True)
    def complete_fixture(self, key):
        require(type(key) is str and key in self._drafts)
        held = self._drafts[key]
        require(held.state == 'reservation')
        self._drafts[key] = replace(held, state='invalidated', text='')
        start = self._time()
        require(held.generation == self._generation)
        fixture = self._valid(key, held)
        require(self._time(start) < held.deadline)
        self._audit('retain', key)
        self._drafts[key] = replace(held, state='held', text=fixture.text)
        return key

    def _grant(self, token, key):
        actor = self._auth(token, 'PV')
        require(type(key) is str)
        grant = self._grants.get(key)
        require(type(grant) is Grant and grant.active and grant.subject == actor and self._time() < grant.deadline)
        return grant

    @operation(reader=True)
    def request_view(self, token, draft_id):
        start = self._time()
        grant = self._grant(token, draft_id)
        held = self._drafts.get(draft_id)
        require(type(held) is Held and held.state == 'held' and self._permit_count < 64)
        self._valid(draft_id, held)
        now = self._time(start)
        require(now < min(grant.deadline, held.deadline))
        self._audit('permit', draft_id)
        permit = secrets.token_hex(16)
        self._permits[permit] = Permit(
            draft_id,
            held.context,
            grant.subject,
            grant.version,
            self._generation,
            min(now + dt.timedelta(seconds=30), grant.deadline, held.deadline),
        )
        self._permit_count += 1
        return permit

    @operation(reader=True)
    def view_fixture(self, token, permit_id):
        actor = self._auth(token, 'PV')
        require(type(permit_id) is str and len(permit_id) == 32)
        permit = self._permits.get(permit_id)
        require(type(permit) is Permit and permit.subject == actor)
        del self._permits[permit_id]
        start = self._time()
        require(start < permit.deadline and permit.generation == self._generation)
        grant = self._grant(token, permit.draft_id)
        require(grant.version == permit.grant_version)
        held = self._drafts[permit.draft_id]
        require(held.state == 'held' and held.context == permit.context)
        fixture = self._valid(permit.draft_id, held)
        payload = canonical(
            dict(
                status='private_draft',
                synthetic=True,
                claim_status='not_assessed',
                release_allowed=False,
                text=held.text,
                aliases=fixture.aliases,
                draft_id=permit.draft_id,
            )
        ).encode()
        require(len(payload) <= 131072)
        self._audit('private_copy', permit.draft_id)
        now = self._time(start)
        require(now < min(permit.deadline, grant.deadline, held.deadline))
        # Built-in append is the final commit, with no subsequent fallible validation or callback.
        event = AuditEvent(len(self._events) + 1, self._session, permit.draft_id, 'private_copy', 'committed')
        self._events.append(event)
        return payload
