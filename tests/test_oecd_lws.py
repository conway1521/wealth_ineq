"""Unit tests for the OECD and LWS ingest scaffolds.

These tests work without any raw data files by mocking the CSV content.
They verify the column-normalisation, Gini rescaling, and
harmonize_frame -> schema flow.
"""

from __future__ import annotations

import io
from pathlib import Path

import pandas as pd
import pytest


# ---------------------------------------------------------------------------
# OECD
# ---------------------------------------------------------------------------

_OECD_CSV = """\
MEASURE,COUNTRY,TIME_PERIOD,OBS_VALUE,UNIT_MEASURE
GINI_NW,AUS,2018,0.621,INDEX
SHARE_TOP10_NW,AUS,2018,0.572,RATIO
SHARE_TOP1_NW,AUS,2018,0.128,RATIO
MEAN_NW,AUS,2018,273400,USD_PPP
MED_NW,AUS,2018,191000,USD_PPP
GINI_NW,CAN,2019,0.720,INDEX
SHARE_TOP10_NW,CAN,2019,0.624,RATIO
GINI_NW,KOR,2017,0.602,INDEX
"""


def _write_oecd_csv(tmp_path: Path) -> Path:
    d = tmp_path / "oecd"
    d.mkdir()
    (d / "WEALTH.csv").write_text(_OECD_CSV)
    return d


def test_oecd_parse(tmp_path, monkeypatch):
    from wealth_gini_atlas.ingest.oecd import parse
    monkeypatch.setenv("WGA_OECD_LOCAL", str(_write_oecd_csv(tmp_path)))
    df = parse()
    assert set(df["country_code"]) == {"AUS", "CAN", "KOR"}
    aus = df[df["country_code"] == "AUS"].iloc[0]
    assert abs(aus["wealth_gini"] - 0.621) < 1e-6
    assert abs(aus["top10_wealth_share"] - 0.572) < 1e-6
    assert abs(aus["top1_wealth_share"] - 0.128) < 1e-6


def test_oecd_harmonize_frame_schema(tmp_path, monkeypatch):
    from wealth_gini_atlas.ingest.oecd import harmonize_frame
    from wealth_gini_atlas.schema import validate
    monkeypatch.setenv("WGA_OECD_LOCAL", str(_write_oecd_csv(tmp_path)))
    df = harmonize_frame()
    assert len(df) == 3                        # AUS, CAN, KOR
    assert (df["source_dataset"] == "OECD").all()
    assert (df["source_priority"] == "tier2").all()
    assert (df["comparability_tier"] == "B").all()
    assert df["wealth_gini"].between(0, 1).all()
    assert validate(df, strict=False) == []


def test_oecd_gini_rescale(tmp_path, monkeypatch):
    """Gini expressed as 0-100 in the source should be rescaled to 0-1."""
    csv = "MEASURE,COUNTRY,TIME_PERIOD,OBS_VALUE\nGINI_NW,DEU,2015,62.1\n"
    d = tmp_path / "oecd"
    d.mkdir()
    (d / "WEALTH.csv").write_text(csv)
    monkeypatch.setenv("WGA_OECD_LOCAL", str(d))
    from wealth_gini_atlas.ingest.oecd import harmonize_frame
    df = harmonize_frame()
    assert abs(df.iloc[0]["wealth_gini"] - 0.621) < 1e-6


def test_oecd_missing_file(tmp_path, monkeypatch):
    monkeypatch.setenv("WGA_OECD_LOCAL", str(tmp_path / "no-oecd"))
    from wealth_gini_atlas.ingest.oecd import harmonize_frame
    with pytest.raises(FileNotFoundError):
        harmonize_frame()


# ---------------------------------------------------------------------------
# LWS
# ---------------------------------------------------------------------------

_LWS_CSV = """\
country_code,year,wave,gini_nw,top10_nw,top1_nw,median_nw,mean_nw
US,2019,lws2019us,0.872,0.738,0.353,68000,875000
US,2016,lws2016us,0.858,0.766,0.388,81000,901000
DE,2014,lws2014de,0.761,0.598,0.218,51000,185000
GB,2018,lws2018gb,0.647,0.560,0.210,107000,289000
CA,2016,lws2016ca,0.729,0.625,0.200,170000,423000
"""


def _write_lws_csv(tmp_path: Path) -> Path:
    d = tmp_path / "lws"
    d.mkdir()
    (d / "lws-gini.csv").write_text(_LWS_CSV)
    return d


def test_lws_parse(tmp_path, monkeypatch):
    from wealth_gini_atlas.ingest.lws import parse
    monkeypatch.setenv("WGA_LWS_LOCAL", str(_write_lws_csv(tmp_path)))
    df = parse()
    assert set(df["country_code"]) == {"US", "DE", "GB", "CA"}
    us = df[df["country_code"] == "US"].sort_values("year")
    assert len(us) == 2
    assert abs(us.iloc[-1]["wealth_gini"] - 0.872) < 1e-6


def test_lws_harmonize_frame_schema(tmp_path, monkeypatch):
    from wealth_gini_atlas.ingest.lws import harmonize_frame
    from wealth_gini_atlas.schema import validate
    monkeypatch.setenv("WGA_LWS_LOCAL", str(_write_lws_csv(tmp_path)))
    df = harmonize_frame()
    assert (df["source_dataset"] == "LWS").all()
    assert (df["source_priority"] == "tier1").all()
    assert (df["comparability_tier"] == "A").all()
    assert df["wealth_gini"].between(0, 1).all()
    assert validate(df, strict=False) == []


def test_lws_gini_rescale_100(tmp_path, monkeypatch):
    csv = "country_code,year,gini_nw\nUS,2019,87.2\n"
    d = tmp_path / "lws"
    d.mkdir()
    (d / "lws.csv").write_text(csv)
    monkeypatch.setenv("WGA_LWS_LOCAL", str(d))
    from wealth_gini_atlas.ingest.lws import harmonize_frame
    df = harmonize_frame()
    assert abs(df.iloc[0]["wealth_gini"] - 0.872) < 1e-6


def test_lws_missing_file(tmp_path, monkeypatch):
    monkeypatch.setenv("WGA_LWS_LOCAL", str(tmp_path / "no-lws"))
    from wealth_gini_atlas.ingest.lws import harmonize_frame
    with pytest.raises(FileNotFoundError):
        harmonize_frame()
