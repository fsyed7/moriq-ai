"""Synthetic fixtures only; no publisher bodies or real credentials."""

from dataclasses import replace

import pytest

from moriq.knowledge.registry import Registry, SourceMetadata, sha256

BODY = b'A thermal bridge transfers heat through a building envelope.\r\n'


@pytest.fixture
def registry():
    return Registry(
        {
            'test-author': ('author', {'author'}),
            'test-reviewer': ('reviewer', {'reviewer'}),
            'test-self-review': ('author', {'reviewer'}),
        },
        local_references={'local:fixture.md'},
    )


@pytest.fixture
def metadata():
    return SourceMetadata(
        source_id='ref-1',
        title='Thermal bridges',
        reference='https://example.org/architecture/thermal-bridges',
        source_type='educational',
        format='text',
        license='CC0-1.0',
        usage_permission='public_redistribution',
        classification='public',
        content_sha256=sha256(BODY),
        revision='1',
        publisher='Synthetic test publisher',
        author='Synthetic fixture author',
        publication_date='2026-10-14',
    )


def approved(registry, metadata, body=BODY):
    record = registry.propose('test-author', replace(metadata, content_sha256=sha256(body)))
    registry.approve('test-reviewer', metadata.source_id, record.document_id)
    return registry.ingest('test-author', metadata.source_id, body)
