"""Tests for the US long-run composite series."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from wealth_gini_atlas.analysis.us_longrun import build_composite


def _make_moments_atlas(tmp_path: Path) -> Path:
    """Write a minimal Moments Atlas parquet for testing."""
    from wealth_gini_atlas.schema import conform

    rows = []
    # DFA: 1989-1995 annual
    for yr in range(1989, 1996):
        rows.append({
            "geo_id": "USA", "geo_name": "United States",
            "geo_level": "country", "year": yr,
            "wealth_concept": "net_wealth",
            "wealth_gini": pd.NA, "wealth_gini_raw": pd.NA,
            "negative_wealth_share": pd.NA,
            "mean_net_wealth": pd.NA, "median_net_wealth": pd.NA,
            "top10_wealth_share": 0.60 + yr * 0.001,
            "top1_wealth_share":  0.22 + yr * 0.0005,
            "bottom50_wealth_share": 0.04,
            "unit_of_analysis": "household", "equivalence_scale": "none",
            "currency": "USD", "source_dataset": "DFA",
            "source_priority": "tier1", "comparability_tier": "B",
            "observed_vs_modeled": "imported",
            "top_tail_flag": "admin_enhanced",
            "method_version": "wga-0.3", "notes": "",
        })
    # SCF: 1989, 1992 (triennial subset)
    for yr, mean, med in [(1989, 436_000, 108_000), (1992, 387_000, 102_000)]:
        rows.append({
            "geo_id": "USA", "geo_name": "United States",
            "geo_level": "country", "year": yr,
            "wealth_concept": "net_wealth",
            "wealth_gini": pd.NA, "wealth_gini_raw": pd.NA,
            "negative_wealth_share": pd.NA,
            "mean_net_wealth": mean, "median_net_wealth": med,
            "top10_wealth_share": 0.671,
            "top1_wealth_share": pd.NA,
            "bottom50_wealth_share": 0.030,
            "unit_of_analysis": "household", "equivalence_scale": "none",
            "currency": "USD_2022", "source_dataset": "SCF",
            "source_priority": "tier1", "comparability_tier": "B",
            "observed_vs_modeled": "imported",
            "top_tail_flag": "survey_only",
            "method_version": "wga-0.3", "notes": "",
        })

    df = conform(pd.DataFrame(rows))
    path = tmp_path / "wealth_moments_atlas_v0.3.0.parquet"
    df.to_parquet(path, index=False)
    return path


def test_build_composite_shape(tmp_path):
    path = _make_moments_atlas(tmp_path)
    comp = build_composite(path)
    # 1989-1995 = 7 annual rows (DFA drives the index)
    assert len(comp) == 7
    assert list(comp["year"]) == list(range(1989, 1996))


def test_build_composite_columns(tmp_path):
    path = _make_moments_atlas(tmp_path)
    comp = build_composite(path)
    for col in ("top1_share", "top10_share", "bottom50_share",
                "top10_share_scf", "top10_gap",
                "mean_net_wealth_scf", "mean_net_wealth_interp",
                "source_shares", "source_moments"):
        assert col in comp.columns, f"missing column: {col}"


def test_dfa_shares_annual(tmp_path):
    """DFA columns should be non-null for all annual rows."""
    comp = build_composite(_make_moments_atlas(tmp_path))
    assert comp["top1_share"].notna().all()
    assert comp["top10_share"].notna().all()
    assert comp["bottom50_share"].notna().all()


def test_scf_triennial_anchor_points(tmp_path):
    """SCF raw columns are non-null only in the two survey years."""
    comp = build_composite(_make_moments_atlas(tmp_path))
    scf_obs = comp["mean_net_wealth_scf"].notna()
    assert scf_obs.sum() == 2
    assert set(comp.loc[scf_obs, "year"]) == {1989, 1992}


def test_interpolation_fills_gap_years(tmp_path):
    """Interpolated mean should be non-null for all years 1989-1992."""
    comp = build_composite(_make_moments_atlas(tmp_path))
    in_range = comp[comp["year"].between(1989, 1992)]
    assert in_range["mean_net_wealth_interp"].notna().all()
    # Interpolated value at 1990 should be between 1989 and 1992 values
    v89 = comp.loc[comp["year"] == 1989, "mean_net_wealth_interp"].iloc[0]
    v90 = comp.loc[comp["year"] == 1990, "mean_net_wealth_interp"].iloc[0]
    v92 = comp.loc[comp["year"] == 1992, "mean_net_wealth_interp"].iloc[0]
    assert v92 < v89                   # wealth fell 1989->1992 in the fixture
    assert v92 <= v90 <= v89


def test_top10_gap_sign(tmp_path):
    """Top-10 gap should be populated where SCF triennial data is present."""
    comp = build_composite(_make_moments_atlas(tmp_path))
    gap_where_scf = comp.loc[comp["top10_share_scf"].notna(), "top10_gap"]
    assert gap_where_scf.notna().all()


def test_source_flags(tmp_path):
    """source_shares is always DFA; source_moments reflects SCF availability."""
    comp = build_composite(_make_moments_atlas(tmp_path))
    assert (comp["source_shares"] == "DFA").all()
    scf_rows = comp[comp["mean_net_wealth_scf"].notna()]
    assert (scf_rows["source_moments"] == "SCF").all()
    interp_rows = comp[comp["mean_net_wealth_scf"].isna()]
    assert (interp_rows["source_moments"] == "SCF_interp").all()
