from dataclasses import replace

import pytest
from conftest import approved

from moriq.knowledge.retrieval import retrieve


def test_returns_provenance_linked_passages(registry, metadata):
    approved(registry, metadata)
    (hit,) = retrieve('What is a thermal bridge?', registry)
    assert hit.chunk.source_id == 'ref-1'
    assert hit.chunk.provenance.metadata.reference == metadata.reference
    assert hit.chunk.provenance.review_status == 'approved'


def test_pending_excluded(registry, metadata):
    registry.propose('test-author', metadata)
    assert retrieve('thermal', registry) == ()


def test_missing_and_empty_queries(registry, metadata):
    approved(registry, metadata)
    assert retrieve('seismic design', registry) == ()
    assert retrieve('', registry) == ()


def test_scope_filters(registry, metadata):
    approved(registry, replace(metadata, jurisdiction='Ontario', code_edition='2024'))
    assert retrieve('thermal', registry, jurisdiction='Quebec') == ()
    assert retrieve('thermal', registry, edition='2012') == ()
    assert len(retrieve('thermal', registry, jurisdiction='Ontario', edition='2024')) == 1


def test_unscoped_source_is_not_a_jurisdiction_match(registry, metadata):
    approved(registry, metadata)
    assert retrieve('thermal', registry, jurisdiction='Ontario') == ()


def test_uploaded_review_flags_never_authorize():
    with pytest.raises(ValueError, match='registry'):
        retrieve('thermal', [{'reviewed': True, 'public': True}])


def test_sort_score_then_id(registry, metadata):
    approved(registry, replace(metadata, source_id='c', title='Building envelope'))
    approved(registry, replace(metadata, source_id='b'))
    approved(registry, replace(metadata, source_id='a'))
    assert [h.chunk.source_id for h in retrieve('thermal bridge', registry)] == ['a', 'b', 'c']


@pytest.mark.parametrize('limit', [0, 21, True, '5'])
def test_max_hits_bound(registry, limit):
    with pytest.raises(ValueError, match='max_hits'):
        retrieve('thermal', registry, max_hits=limit)


def test_withdrawn_sources_disappear(registry, metadata):
    approved(registry, metadata)
    registry.withdraw('test-reviewer', metadata.source_id)
    assert retrieve('thermal', registry) == ()
