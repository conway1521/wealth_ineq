"""Integration tests against real SCF and DFA source files.

These tests run only when the raw data files are present locally
(data/raw/scf/ and data/raw/dfa/). They are skipped in CI environments
that don't have the raw files committed.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

RAW_SCF = Path(__file__).resolve().parents[1] / "data" / "raw" / "scf"
RAW_DFA = Path(__file__).resolve().parents[1] / "data" / "raw" / "dfa"

scf_available = pytest.mark.skipif(
    not (RAW_SCF / "interactive_bulletin_charts_all_mean.csv").exists(),
    reason="SCF raw files not present",
)
dfa_available = pytest.mark.skipif(
    not (RAW_DFA / "dfa-networth-shares.csv").exists(),
    reason="DFA raw files not present",
)


@scf_available
def test_scf_parse_shape_and_values():
    from wealth_gini_atlas.ingest.scf import parse
    df = parse()
    assert len(df) == 12                   # 12 triennial SCF surveys
    assert set(df["year"]) >= {1989, 2001, 2016, 2022}

    # Mean > median everywhere (right-skewed distribution)
    assert (df["mean_net_wealth"] > df["median_net_wealth"]).all()

    # Top-10 share in [0.60, 0.85] -- plausible US range
    assert df["top10_share"].between(0.60, 0.85).all()

    # Bottom-50 share in [0.00, 0.10]
    assert df["bottom50_share"].between(0.0, 0.10).all()

    # Top-10 > bottom-50 always
    assert (df["top10_share"] > df["bottom50_share"]).all()


@scf_available
def test_scf_harmonize_frame_schema():
    from wealth_gini_atlas.ingest.scf import harmonize_frame
    from wealth_gini_atlas.schema import validate
    df = harmonize_frame()
    assert len(df) == 12
    assert (df["geo_id"] == "USA").all()
    assert (df["source_dataset"] == "SCF").all()
    assert df["wealth_gini"].isna().all()
    assert df["top1_wealth_share"].isna().all()    # not available from chartbook
    issues = validate(df, strict=False, mode="moments_atlas")
    assert issues == []


@dfa_available
def test_dfa_parse_shape_and_values():
    from wealth_gini_atlas.ingest.dfa import parse
    df = parse()
    assert len(df) >= 36       # 1989Q4..2024Q4 at minimum
    assert df["year"].min() == 1989
    assert df["year"].max() >= 2024

    # Shares plausible for the US
    assert df["top1_share"].between(0.20, 0.40).all()
    assert df["top10_share"].between(0.55, 0.80).all()
    assert df["bottom50_share"].between(0.0, 0.06).all()

    # Nesting: top1 < top10 always
    assert (df["top1_share"] < df["top10_share"]).all()


@dfa_available
def test_dfa_harmonize_frame_schema():
    from wealth_gini_atlas.ingest.dfa import harmonize_frame
    from wealth_gini_atlas.schema import validate
    df = harmonize_frame()
    assert (df["geo_id"] == "USA").all()
    assert (df["source_dataset"] == "DFA").all()
    assert df["wealth_gini"].isna().all()
    assert df["mean_net_wealth"].isna().all()    # DFA doesn't supply per-HH mean
    issues = validate(df, strict=False, mode="moments_atlas")
    assert issues == []


@pytest.mark.skipif(
    not (RAW_SCF / "interactive_bulletin_charts_all_mean.csv").exists()
    or not (RAW_DFA / "dfa-networth-shares.csv").exists(),
    reason="SCF and/or DFA raw files not present",
)
def test_scf_dfa_cross_check():
    """Top-10 shares should be directionally consistent across sources."""
    from wealth_gini_atlas.ingest.dfa import parse as dfa_parse
    from wealth_gini_atlas.ingest.scf import parse as scf_parse

    scf = scf_parse().set_index("year")
    dfa = dfa_parse().set_index("year")
    common = sorted(set(scf.index) & set(dfa.index))
    assert common, "No overlapping years between SCF and DFA"

    for yr in common:
        scf_t10 = scf.loc[yr, "top10_share"]
        dfa_t10 = dfa.loc[yr, "top10_share"]
        # Directional check: both show top-10 > 50% of wealth
        assert scf_t10 > 0.50, f"{yr}: SCF top10={scf_t10:.3f}"
        assert dfa_t10 > 0.50, f"{yr}: DFA top10={dfa_t10:.3f}"
        # They should be within 15pp of each other (same concept, different method)
        assert abs(scf_t10 - dfa_t10) < 0.15, (
            f"{yr}: SCF top10={scf_t10:.3f} vs DFA top10={dfa_t10:.3f} "
            f"diverge by more than 15pp"
        )
