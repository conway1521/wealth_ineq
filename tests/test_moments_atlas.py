"""Moments Atlas: harmonizer split + schema validator + writer.

The Moments Atlas holds rows where the source publishes
distributional moments (mean, median, top-shares, negative-share)
but no Gini. SCF chartbook and DFA are the v0.3+ contributors;
WID country-years that publish only shares / mean also land here.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from wealth_gini_atlas.harmonize.national import split_gini_and_moments
from wealth_gini_atlas.release.build import write_moments
from wealth_gini_atlas.schema import SchemaError, conform, validate


def _row(**overrides):
    base = {
        "geo_id": "USA", "geo_name": "United States", "geo_level": "country",
        "year": 2022, "wealth_concept": "net_wealth",
        "wealth_gini": pd.NA, "wealth_gini_raw": pd.NA,
        "mean_net_wealth": 1_063_700.0,
        "median_net_wealth": 192_700.0,
        "top10_wealth_share": 0.694,
        "top1_wealth_share":  0.302,
        "unit_of_analysis": "household", "equivalence_scale": "none",
        "source_dataset": "SCF", "source_priority": "tier1",
        "comparability_tier": "B", "observed_vs_modeled": "imported",
        "method_version": "wga-0.2",
    }
    base.update(overrides)
    return base


def test_split_separates_gini_from_moments():
    rows = [
        _row(),                                      # SCF moments-only
        _row(source_dataset="DFA"),                  # DFA moments-only
        _row(source_dataset="WID", wealth_gini=0.85, wealth_gini_raw=0.85),
    ]
    df = conform(pd.DataFrame(rows))
    gini, moments = split_gini_and_moments(df)
    assert len(gini) == 1
    assert len(moments) == 2
    assert set(gini["source_dataset"]) == {"WID"}
    assert set(moments["source_dataset"]) == {"SCF", "DFA"}


def test_split_drops_rows_with_neither_gini_nor_moments():
    """A row that's null on Gini AND on every other moment is orphan."""
    rows = [
        _row(
            mean_net_wealth=pd.NA, median_net_wealth=pd.NA,
            top10_wealth_share=pd.NA, top1_wealth_share=pd.NA,
        ),
    ]
    df = conform(pd.DataFrame(rows))
    gini, moments = split_gini_and_moments(df)
    assert gini.empty and moments.empty


def test_moments_atlas_validates_in_moments_mode():
    df = conform(pd.DataFrame([_row()]))
    issues = validate(df, strict=False, mode="moments_atlas")
    assert issues == []


def test_moments_atlas_fails_default_validation():
    """The default mode (gini_atlas) requires wealth_gini -> moments fail."""
    df = conform(pd.DataFrame([_row()]))
    with pytest.raises(SchemaError):
        validate(df, strict=True)   # default mode = gini_atlas


def test_moments_mode_flags_rows_with_no_moments():
    df = conform(pd.DataFrame([_row(
        mean_net_wealth=pd.NA, median_net_wealth=pd.NA,
        top10_wealth_share=pd.NA, top1_wealth_share=pd.NA,
        bottom50_wealth_share=pd.NA, negative_wealth_share=pd.NA,
    )]))
    issues = validate(df, strict=False, mode="moments_atlas")
    assert any("no non-Gini moments" in i for i in issues)


def test_writer_emits_companion_artifact(tmp_path):
    df = conform(pd.DataFrame([
        _row(year=2019),
        _row(year=2022),
        _row(source_dataset="DFA", year=2022, top1_wealth_share=0.305,
             top10_wealth_share=0.692, mean_net_wealth=1_050_000.0,
             median_net_wealth=pd.NA),
    ]))
    manifest = write_moments(df, tmp_path, version="0.3.0-test")
    assert manifest["name"].startswith("Wealth Moments Atlas")
    assert manifest["n_rows"] == 3

    csv = pd.read_csv(tmp_path / "wealth_moments_atlas_v0.3.0-test.csv")
    pq = pd.read_parquet(tmp_path / "wealth_moments_atlas_v0.3.0-test.parquet")
    assert len(csv) == len(pq) == 3
    assert csv["wealth_gini"].isna().all()
