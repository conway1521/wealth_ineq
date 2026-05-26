"""Properties of the Gini implementation.

Test cases include the textbook benchmarks (perfect equality,
maximum inequality) plus an analytic check against a uniform
distribution: U[0, a] has Gini = 1/3 in the continuum limit.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from wealth_gini_atlas.gini import (
    bottom_share,
    gini,
    negative_share,
    top_share,
    weighted_mean,
    weighted_median,
)


def test_perfect_equality_is_zero():
    assert gini([5, 5, 5, 5]) == pytest.approx(0.0, abs=1e-12)


def test_one_owns_everything_approaches_one():
    g = gini([0, 0, 0, 0, 100])
    # For n=5 with one unit holding everything the closed-form value is (n-1)/n = 0.8
    assert g == pytest.approx(0.8, abs=1e-12)


def test_uniform_limit_is_one_third():
    rng = np.random.default_rng(0)
    sample = rng.uniform(0.0, 1.0, size=200_000)
    assert gini(sample) == pytest.approx(1.0 / 3.0, abs=5e-3)


def test_scale_invariance():
    rng = np.random.default_rng(1)
    sample = rng.lognormal(mean=0, sigma=1, size=10_000)
    assert gini(sample) == pytest.approx(gini(sample * 137.0), abs=1e-10)


def test_weights_are_equivalent_to_replication():
    x = np.array([1.0, 2.0, 3.0, 4.0])
    w = np.array([1, 2, 3, 4], dtype=float)
    replicated = np.repeat(x, w.astype(int))
    assert gini(x, weights=w) == pytest.approx(gini(replicated), abs=1e-12)


def test_negative_handling_zero_clips_to_unit_interval():
    x = [-50, -10, 0, 5, 20, 100]
    g = gini(x, negative_handling="zero")
    assert 0.0 <= g <= 1.0


def test_negative_handling_keep_leaves_unit_interval():
    # When the distribution contains negatives, the raw Gini is not
    # guaranteed to lie in [0, 1]; this is exactly why the headline
    # series zeroes negatives out before computing the Gini.
    x = [-100, 1, 1, 1]
    g_keep = gini(x, negative_handling="keep")
    g_zero = gini(x, negative_handling="zero")
    assert not (0.0 <= g_keep <= 1.0)   # raw value escapes the unit interval
    assert 0.0 <= g_zero <= 1.0          # headline value stays well-behaved


def test_top10_share_matches_definition():
    # 90 zeros and 10 ones -> top 10% holds 100% of the wealth.
    x = [0.0] * 90 + [1.0] * 10
    assert top_share(x, top_fraction=0.1) == pytest.approx(1.0, abs=1e-12)


def test_top_share_continuum_uniform():
    rng = np.random.default_rng(2)
    x = rng.uniform(0, 1, size=200_000)
    # For U(0, 1) the top-10% share is the integral from 0.9 to 1 of x dx
    # divided by 0.5 -> (1 - 0.81)/2 / 0.5 = 0.19.
    assert top_share(x, top_fraction=0.1) == pytest.approx(0.19, abs=5e-3)


def test_bottom_share_complement_of_top():
    rng = np.random.default_rng(3)
    x = rng.lognormal(0, 0.5, size=50_000)
    assert bottom_share(x, bottom_fraction=0.5) + top_share(x, top_fraction=0.5) \
        == pytest.approx(1.0, abs=1e-10)


def test_negative_share_weighted():
    x = [-1.0, -2.0, 5.0, 5.0, 5.0]
    w = [1.0,  1.0,  1.0, 1.0, 1.0]
    assert negative_share(x, weights=w) == pytest.approx(0.4, abs=1e-12)


def test_weighted_mean_and_median():
    x = [1.0, 2.0, 3.0, 4.0, 5.0]
    w = [1.0, 1.0, 1.0, 1.0, 1.0]
    assert weighted_mean(x, w) == pytest.approx(3.0)
    assert weighted_median(x, w) == pytest.approx(3.0)


def test_gini_handles_empty_input():
    assert math.isnan(gini([]))
    assert math.isnan(top_share([], top_fraction=0.1))
