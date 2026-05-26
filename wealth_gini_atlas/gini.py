"""Weighted Gini coefficient and distributional shares for wealth data.

The Gini is implemented in the classical sorted-cumulative form.
With unit weights it reduces to

    G = sum_i (2 i - n - 1) * x_i  /  ( n * sum_i x_i )

after sorting x ascending. We extend this to non-negative weights using
the standard weighted formulation, which is mathematically equivalent
to integrating the Lorenz gap.

Wealth-specific handling
------------------------

Wealth distributions frequently contain zero and negative values
(households with more liabilities than assets). Applying the raw
formula to a distribution with negative values can yield Gini > 1,
which breaks the [0, 1] interpretation users expect from a public-facing
index. We therefore expose a `negative_handling` flag:

* "zero"  — set negative values to 0 (project default for the headline
            public series; see methods.md).
* "keep"  — leave negatives in place (advanced users / `wealth_gini_raw`).
* "drop"  — drop negative-wealth units entirely (discouraged; biases mean).

We also expose `negative_share()` so the upstream pipeline can store the
share of units with negative net wealth alongside the headline Gini.
"""

from __future__ import annotations

from typing import Literal

import numpy as np

NegativeHandling = Literal["zero", "keep", "drop"]


def _prep(values: np.ndarray,
          weights: np.ndarray | None,
          negative_handling: NegativeHandling) -> tuple[np.ndarray, np.ndarray]:
    x = np.asarray(values, dtype=float).ravel()
    if weights is None:
        w = np.ones_like(x)
    else:
        w = np.asarray(weights, dtype=float).ravel()
        if w.shape != x.shape:
            raise ValueError("weights and values must have the same shape")
        if (w < 0).any():
            raise ValueError("weights must be non-negative")

    # Drop NaN / non-finite from either side
    mask = np.isfinite(x) & np.isfinite(w) & (w > 0)
    x, w = x[mask], w[mask]

    if negative_handling == "zero":
        x = np.where(x < 0, 0.0, x)
    elif negative_handling == "drop":
        m = x >= 0
        x, w = x[m], w[m]
    elif negative_handling == "keep":
        pass
    else:
        raise ValueError(f"unknown negative_handling: {negative_handling!r}")

    return x, w


def gini(values, weights=None, *, negative_handling: NegativeHandling = "zero") -> float:
    """Weighted Gini coefficient.

    Returns NaN for empty input or for distributions whose weighted mean
    is zero (degenerate / undefined).
    """
    x, w = _prep(np.asarray(values), weights, negative_handling)
    if x.size == 0:
        return float("nan")

    order = np.argsort(x, kind="mergesort")
    x = x[order]
    w = w[order]

    cw = np.cumsum(w)
    total_w = cw[-1]
    if total_w == 0:
        return float("nan")

    weighted_sum = float(np.sum(w * x))
    if weighted_sum == 0:
        return float("nan")

    # Weighted Gini = 1 - 2 * weighted area under the Lorenz curve.
    # Equivalent compact form:
    #   G = ( sum_i w_i x_i ( 2 F_i - 1 ) ) / mean
    # where F_i is the weighted CDF position at observation i.
    # We use the closed form for sorted x:
    #   G = ( 2 * sum_i w_i x_i C_i  -  sum_i w_i x_i ) / ( total_w * mean )  - 1/total_w * ...
    # The numerically stable identity below matches the unweighted reduction.
    cum_wx = np.cumsum(w * x)
    # Numerator: 2 * sum_i w_i x_i * (cum_w_i - w_i/2) - total_w * sum_i w_i x_i
    # Equivalent expression:
    numer = float(np.sum(w * (2.0 * cw - w) * x) - total_w * weighted_sum)
    denom = float(total_w * weighted_sum)
    g = numer / denom
    # Numerical safety on the upper boundary when negatives are zeroed:
    if -1e-12 < g < 0:
        g = 0.0
    return g


def top_share(values, weights=None, *, top_fraction: float,
              negative_handling: NegativeHandling = "zero") -> float:
    """Wealth share held by the top `top_fraction` of units (weighted).

    `top_fraction` is in (0, 1); e.g. 0.1 returns the top-10% share.
    """
    if not 0 < top_fraction < 1:
        raise ValueError("top_fraction must be in (0, 1)")

    x, w = _prep(np.asarray(values), weights, negative_handling)
    if x.size == 0:
        return float("nan")

    order = np.argsort(x, kind="mergesort")
    x, w = x[order], w[order]

    total_w = float(w.sum())
    cutoff_w = (1.0 - top_fraction) * total_w
    cw = np.cumsum(w)

    # Linearly split the boundary observation so the answer is smooth.
    idx = int(np.searchsorted(cw, cutoff_w, side="right"))
    if idx >= x.size:
        return 0.0

    # Weight of the boundary unit that falls inside the top group:
    w_in_top = cw[idx] - cutoff_w
    top_wealth = float(w_in_top * x[idx] + np.sum(w[idx + 1:] * x[idx + 1:]))
    total_wealth = float(np.sum(w * x))
    if total_wealth == 0:
        return float("nan")
    return top_wealth / total_wealth


def bottom_share(values, weights=None, *, bottom_fraction: float,
                 negative_handling: NegativeHandling = "zero") -> float:
    """Wealth share held by the bottom `bottom_fraction` of units (weighted)."""
    if not 0 < bottom_fraction < 1:
        raise ValueError("bottom_fraction must be in (0, 1)")
    # Computed via 1 - top_share at the complementary cutoff.
    return 1.0 - top_share(values, weights,
                           top_fraction=1.0 - bottom_fraction,
                           negative_handling=negative_handling)


def negative_share(values, weights=None) -> float:
    """Share of units (by weight) with strictly negative net wealth."""
    x = np.asarray(values, dtype=float).ravel()
    if weights is None:
        w = np.ones_like(x)
    else:
        w = np.asarray(weights, dtype=float).ravel()
    mask = np.isfinite(x) & np.isfinite(w) & (w > 0)
    x, w = x[mask], w[mask]
    if x.size == 0:
        return float("nan")
    return float(w[x < 0].sum() / w.sum())


def weighted_mean(values, weights=None) -> float:
    x = np.asarray(values, dtype=float).ravel()
    if weights is None:
        w = np.ones_like(x)
    else:
        w = np.asarray(weights, dtype=float).ravel()
    mask = np.isfinite(x) & np.isfinite(w) & (w > 0)
    x, w = x[mask], w[mask]
    if x.size == 0:
        return float("nan")
    return float((w * x).sum() / w.sum())


def weighted_median(values, weights=None) -> float:
    x = np.asarray(values, dtype=float).ravel()
    if weights is None:
        w = np.ones_like(x)
    else:
        w = np.asarray(weights, dtype=float).ravel()
    mask = np.isfinite(x) & np.isfinite(w) & (w > 0)
    x, w = x[mask], w[mask]
    if x.size == 0:
        return float("nan")
    order = np.argsort(x, kind="mergesort")
    x, w = x[order], w[order]
    cw = np.cumsum(w)
    half = 0.5 * cw[-1]
    return float(x[np.searchsorted(cw, half, side="left")])
