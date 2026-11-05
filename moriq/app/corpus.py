"""Host-owned registry for reviewed sources. It holds one clearly fictional code sample.

The sample exercises the code-evidence path only under the fictional TESTLAND
jurisdiction. Real code texts need rights and review before they belong here.
"""

from moriq.knowledge.registry import Registry, SourceMetadata, sha256

_BODY = (
    'SYNTHETIC SAMPLE, not a real code. In the fictional TESTLAND TEST-v1 code, an egress stair '
    'requires a fictional minimum width of 1 test unit.'
).encode('utf-8')


def build_registry():
    registry = Registry({'host-author': ('author', {'author'}), 'host-reviewer': ('reviewer', {'reviewer'})})
    meta = SourceMetadata(
        'SYNTHETIC-CODE', 'SYNTHETIC SAMPLE: TESTLAND stair note', 'https://example.org/moriq-synthetic', 'code', 'text',
        'CC0-1.0', 'public_redistribution', 'public', sha256(_BODY), 'synthetic-v1',
        jurisdiction='TESTLAND', code_edition='TEST-v1',
    )
    record = registry.propose('host-author', meta)
    registry.approve('host-reviewer', 'SYNTHETIC-CODE', record.document_id)
    registry.ingest('host-author', 'SYNTHETIC-CODE', _BODY)
    return registry
