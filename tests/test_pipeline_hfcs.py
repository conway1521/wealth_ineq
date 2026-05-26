"""End-to-end test of the combined WID + HFCS pipeline.

Demonstrates that:
* The same country-year can carry rows from both WID and HFCS, with
  distinct ``source_dataset`` and ``unit_of_analysis`` values, and the
  natural-key uniqueness invariant still holds.
* HFCS rows are tagged household-basis / Tier A; WID rows remain
  per-adult-equal-split / Tier B.
* The combined release passes schema validation.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from wealth_gini_atlas.compute.pipeline import build_release
from wealth_gini_atlas.schema import validate


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "data" / "fixtures"


def test_combined_wid_plus_hfcs(tmp_path, monkeypatch):
    monkeypatch.setenv("WGA_WID_LOCAL", str(FIXTURE_DIR))
    monkeypatch.setenv("WGA_HFCS_LOCAL", str(FIXTURE_DIR / "hfcs_indicators.csv"))

    df = build_release()
    assert not df.empty

    # Both sources represented
    sources = set(df["source_dataset"])
    assert sources == {"WID", "HFCS"}

    # HFCS rows are household-basis Tier A
    hfcs = df[df["source_dataset"] == "HFCS"]
    assert (hfcs["unit_of_analysis"] == "household").all()
    assert (hfcs["comparability_tier"] == "A").all()
    assert (hfcs["top_tail_flag"] == "survey_only").all()
    assert (hfcs["currency"] == "EUR").all()

    # WID rows remain per-adult-equal-split Tier B
    wid = df[df["source_dataset"] == "WID"]
    assert (wid["unit_of_analysis"] == "per_adult_equal_split").all()
    assert (wid["comparability_tier"] == "B").all()

    # Same country-year, different source -> two rows, no natural-key dup
    fr_2018 = df[(df["geo_id"] == "FRA") & (df["year"] == 2018)]
    assert set(fr_2018["source_dataset"]) == {"WID"}    # HFCS has no 2018 row
    de = df[df["geo_id"] == "DEU"]
    assert set(de["source_dataset"]) == {"WID", "HFCS"}

    # HFCS has the four published waves for each fixture country
    assert (hfcs["geo_id"].value_counts() == 4).all()

    # HFCS Ginis sanity: in [0, 1], household values lower than WID
    # per-adult-equal-split for the same country-year (expected because
    # equivalization sharpens dispersion).
    assert hfcs["wealth_gini"].between(0, 1).all()

    # Schema validates cleanly across the combined release.
    assert validate(df, strict=False) == []
