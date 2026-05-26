"""Integration test for the HFCS Statistical Tables XLSX parser.

Skipped when the workbooks are not checked out (e.g. in a sparse
clone). When run, exercises every supported sheet (J4, F3, A1, A2)
across all four waves and checks the per-row signal.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from wealth_gini_atlas.ingest.hfcs import parse_workbooks


RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw" / "hfcs"


def _have_workbooks() -> bool:
    return any(RAW_DIR.glob("*.xlsx"))


@pytest.mark.skipif(not _have_workbooks(),
                    reason="HFCS workbooks not present in data/raw/hfcs/")
def test_parse_workbooks_extracts_all_four_waves():
    df = parse_workbooks(RAW_DIR)

    # Country growth across waves: 15 -> 20 -> 22 -> 22 (as new EU members
    # joined the survey). Allow for ECB editorial corrections.
    counts_by_wave = df.groupby("wave").size()
    assert counts_by_wave.loc[1] == 15
    assert counts_by_wave.loc[2] == 20
    assert counts_by_wave.loc[3] == 22
    assert counts_by_wave.loc[4] == 22

    # Every (country, wave) row has a Gini value -- HFCS J4 publishes it
    # for every country in every wave.
    assert df["gini"].notna().all()

    # Gini values within plausible HFCS range (lowest is SK at ~0.46,
    # highest is DE / NL at ~0.78).
    assert df["gini"].between(0.40, 0.85).all()

    # Top1% is not published in the workbook -> all null.
    assert df["top1_share"].isna().all()

    # Top10 share is always >= top5 share where both exist.
    have_both = df["top10_share"].notna() & df["top5_share"].notna()
    assert (df.loc[have_both, "top10_share"]
            >= df.loc[have_both, "top5_share"]).all()

    # Mean net wealth is in EUR (not EUR thousands) -- check magnitude.
    # HFCS published euro-area means are in the ~250k-300k EUR band.
    means = df["mean_net_wealth"].dropna()
    assert means.median() > 50_000
    assert means.median() < 1_000_000

    # Negative wealth share looks like a fraction (0..1), not a percentage.
    neg = df["neg_wealth_share"].dropna()
    assert (neg >= 0).all() and (neg <= 0.5).all()


@pytest.mark.skipif(not _have_workbooks(),
                    reason="HFCS workbooks not present in data/raw/hfcs/")
def test_de_gini_progression_matches_published():
    """Germany Gini across waves should reproduce published HFCS values."""
    df = parse_workbooks(RAW_DIR)
    de = df[df["country"] == "DE"].sort_values("wave")
    assert len(de) == 4
    # Published HFCS DE Ginis: ~0.76, ~0.76, ~0.74, ~0.73 across waves 1-4.
    ginis = de["gini"].tolist()
    assert abs(ginis[0] - 0.758) < 0.01
    assert abs(ginis[1] - 0.762) < 0.01
    assert abs(ginis[2] - 0.739) < 0.01
    assert abs(ginis[3] - 0.727) < 0.01
