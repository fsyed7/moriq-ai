"""Pure evaluation arithmetic. No authority decisions or runtime ranking."""

from math import ceil
from statistics import mean, median


def ranking(gold, returned, k):
    assert k > 0 and len(returned) == len(set(returned))
    relevant = set(gold)
    hits = len(relevant.intersection(returned[:k]))
    return dict(
        precision=hits / k,
        recall=hits / len(relevant) if relevant else None,
        rr=next((1 / i for i, p in enumerate(returned[:k], 1) if p in relevant), 0) if relevant else None,
    )


def quantiles(samples):
    assert samples
    return dict(
        n=len(samples), p50=median(samples), p95=sorted(samples)[ceil(0.95 * len(samples)) - 1], max=max(samples)
    )


def allocation(baseline, current, peak):
    assert 0 <= baseline <= peak and 0 <= current <= peak
    return peak - baseline


def aggregate(rows):
    return {
        key: mean(r[key] for r in rows if r[key] is not None) if any(r[key] is not None for r in rows) else None
        for key in ('precision', 'recall', 'rr')
    }
