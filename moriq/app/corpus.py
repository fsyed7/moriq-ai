"""Host-owned registry holding clearly synthetic sources only.

Real MORIQ documents need the owner's rights and an independent reviewer, so none
are ingested here. These samples exercise the evidence path and say so in their text.
"""

from moriq.knowledge.registry import Registry, SourceMetadata, sha256

_SAMPLES = (
    {
        'source_id': 'SYNTHETIC-COURTYARD',
        'title': 'SYNTHETIC SAMPLE: courtyard shading note',
        'source_type': 'guidance',
        'body': (
            'SYNTHETIC SAMPLE, not real guidance and not a MORIQ document. A shaded courtyard threshold '
            'can slow the transition between arrival and interior. Compare shade, circulation and material '
            'continuity at design review, and record open questions rather than performance claims.'
        ),
    },
    {
        'source_id': 'SYNTHETIC-CODE',
        'title': 'SYNTHETIC SAMPLE: TESTLAND stair note',
        'source_type': 'code',
        'jurisdiction': 'TESTLAND',
        'edition': 'TEST-v1',
        'body': (
            'SYNTHETIC SAMPLE, not a real code. In the fictional TESTLAND TEST-v1 code, an egress stair '
            'requires a fictional minimum width of 1 test unit.'
        ),
    },
)


def build_registry():
    registry = Registry({'host-author': ('author', {'author'}), 'host-reviewer': ('reviewer', {'reviewer'})})
    for sample in _SAMPLES:
        body = sample['body'].encode('utf-8')
        meta = SourceMetadata(
            sample['source_id'], sample['title'], 'https://example.org/moriq-synthetic', sample['source_type'], 'text',
            'CC0-1.0', 'public_redistribution', 'public', sha256(body), 'synthetic-v1',
            jurisdiction=sample.get('jurisdiction'), code_edition=sample.get('edition'),
        )
        record = registry.propose('host-author', meta)
        registry.approve('host-reviewer', sample['source_id'], record.document_id)
        registry.ingest('host-author', sample['source_id'], body)
    return registry
