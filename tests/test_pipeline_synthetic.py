"""End-to-end ingest -> harmonize -> release using bundled fixtures.

Proves that the v0.1 pipeline produces a schema-conformant release
artifact without any outbound network access.
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

from wealth_gini_atlas.compute.pipeline import build_release
from wealth_gini_atlas.release.build import write as write_release
from wealth_gini_atlas.schema import validate


FIXTURE_DIR = Path(__file__).resolve().parents[1] / "data" / "fixtures"


def test_end_to_end_with_fixtures(tmp_path, monkeypatch):
    monkeypatch.setenv("WGA_WID_LOCAL", str(FIXTURE_DIR))
    # Scope this test to the WID synthetic fixtures only. Without this
    # the pipeline would also pick up the real HFCS workbooks that ship
    # under data/raw/hfcs/.
    monkeypatch.setenv("WGA_HFCS_LOCAL", str(tmp_path / "no-hfcs.csv"))

    df = build_release()
    assert not df.empty

    # Five countries (FRA, DEU, USA, ESP, ITA), three observations each.
    assert len(df) == 15
    assert set(df["geo_id"]) == {"FRA", "DEU", "USA", "ESP", "ITA"}

    # Gini stays in [0, 1] for all rows.
    g = df["wealth_gini"].astype(float)
    assert (g >= 0).all() and (g <= 1).all()

    # Shares look like 0..1 fractions, not 0..100 percentages.
    assert df["top10_wealth_share"].dropna().between(0, 1).all()
    assert df["top1_wealth_share"].dropna().between(0, 1).all()
    assert df["bottom50_wealth_share"].dropna().between(0, 1).all()

    # Right-skew: mean >= median for every row.
    assert (df["mean_net_wealth"] >= df["median_net_wealth"]).all()

    # Nested-percentile consistency: top1 <= top10 for every row.
    assert (df["top1_wealth_share"] <= df["top10_wealth_share"]).all()

    # Schema validates cleanly, including the internal consistency checks.
    assert validate(df, strict=False) == []

    # Release artifacts round-trip via CSV and Parquet.
    manifest = write_release(df, tmp_path, version="0.1.0-test")
    assert manifest["n_rows"] == 15
    assert manifest["n_countries"] == 5
    assert manifest["sources"] == ["WID"]

    csv = pd.read_csv(tmp_path / "wealth_gini_atlas_v0.1.0-test.csv")
    pq = pd.read_parquet(tmp_path / "wealth_gini_atlas_v0.1.0-test.parquet")
    assert len(csv) == len(pq) == 15
