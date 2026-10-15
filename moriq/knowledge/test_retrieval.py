from datetime import date

import pytest

from retrieval import Source, retrieve


def source(source_id="ref-1", **changes):
    fields = dict(
        source_id=source_id,
        title="Thermal bridges",
        origin_url="https://example.org/architecture/thermal-bridges",
        excerpt="A thermal bridge transfers heat through a building envelope.",
        public=True,
        reviewed=True,
        reviewed_on=date(2026, 10, 14),
        jurisdiction=None,
        edition=None,
    )
    fields.update(changes)
    return Source(**fields)


def test_returns_citable_passages():
    hits = retrieve("What is a thermal bridge?", [source()])
    assert len(hits) == 1
    assert hits[0].source_id == "ref-1"
    assert hits[0].origin_url.startswith("https://")


def test_unreviewed_and_private_are_excluded():
    assert retrieve("thermal bridge", [source(reviewed=False, reviewed_on=None), source("private", public=False)]) == ()


def test_missing_matches_are_empty():
    assert retrieve("seismic design", [source()]) == ()


def test_jurisdiction_must_match_exactly():
    assert retrieve("thermal bridge", [source(jurisdiction="Ontario")], jurisdiction="Quebec") == ()
    assert len(retrieve("thermal bridge", [source(jurisdiction="Ontario")], jurisdiction="Ontario")) == 1


def test_duplicate_ids_are_rejected():
    with pytest.raises(ValueError, match="duplicate"):
        retrieve("thermal", [source(), source()])


def test_unreviewed_metadata_is_not_allowed_to_impersonate_review():
    with pytest.raises(ValueError, match="review date"):
        source(reviewed_on=None)


def test_invalid_identifiers_and_urls():
    with pytest.raises(ValueError, match="source id"):
        source(source_id="../bad")
    with pytest.raises(ValueError, match="HTTPS"):
        source(origin_url="http://example.org")


def test_sorted_by_score_then_id():
    a = source("b", title="Building envelope")
    b = source("a", title="Thermal bridges")
    assert [h.source_id for h in retrieve("thermal bridge", [a, b])] == ["a", "b"]


def test_max_hits_bound():
    with pytest.raises(ValueError, match="max_hits"):
        retrieve("thermal", [source()], max_hits=0)
