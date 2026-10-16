from dataclasses import replace

import pytest
from conftest import BODY, approved

from moriq.knowledge.retrieval import retrieve


def test_returns_provenance_linked_passages(registry, metadata):
    approved(registry, metadata)
    (hit,) = retrieve('What is a thermal bridge?', registry).hits
    assert hit.chunk.source_id == 'ref-1'
    assert hit.chunk.provenance.metadata.reference == metadata.reference
    assert hit.chunk.provenance.review_status == 'approved'


def test_pending_excluded(registry, metadata):
    registry.propose('test-author', metadata)
    assert retrieve('thermal', registry).hits == ()


def test_missing_and_empty_queries(registry, metadata):
    approved(registry, metadata)
    assert retrieve('seismic design', registry).hits == ()
    assert retrieve('', registry).hits == ()


def test_scope_filters(registry, metadata):
    approved(registry, replace(metadata, jurisdiction='Ontario', code_edition='2024'))
    assert retrieve('thermal', registry, jurisdiction='Quebec').hits == ()
    assert retrieve('thermal', registry, edition='2012').hits == ()
    assert len(retrieve('thermal', registry, jurisdiction='Ontario', edition='2024').hits) == 1


def test_unscoped_source_is_not_a_jurisdiction_match(registry, metadata):
    approved(registry, metadata)
    assert retrieve('thermal', registry, jurisdiction='Ontario').hits == ()


def test_uploaded_review_flags_never_authorize():
    assert retrieve('thermal', [{'reviewed': True, 'public': True}]).status == 'invalid_request'


def test_sort_score_then_id(registry, metadata):
    approved(registry, replace(metadata, source_id='c', title='Building envelope'), BODY + b' c')
    approved(registry, replace(metadata, source_id='b'), BODY + b' b')
    approved(registry, replace(metadata, source_id='a'), BODY + b' a')
    assert [h.chunk.source_id for h in retrieve('thermal bridge', registry).hits] == ['a', 'b', 'c']


@pytest.mark.parametrize('limit', [0, 21, True, '5'])
def test_max_hits_bound(registry, limit):
    assert retrieve('thermal', registry, max_hits=limit).status == 'invalid_request'


def test_withdrawn_sources_disappear(registry, metadata):
    approved(registry, metadata)
    registry.withdraw('test-reviewer', metadata.source_id)
    assert retrieve('thermal', registry).hits == ()
