"""Household Finance and Consumption Survey (HFCS) ingest.

The ECB / Eurosystem HFCS publishes harmonized household wealth
distributional indicators across (currently four) waves for the euro
area plus several non-euro EU members. HFCS is the strongest source
for Tier-A, household-basis wealth inequality in Europe -- the
survey instrument and concept boundaries are explicitly aligned
across countries.

Source
------

Headline distributional results are published by the ECB at
    https://www.ecb.europa.eu/stats/ecb_surveys/hfcs/html/index.en.html
and individual series are downloadable as CSV from the ECB Data
Portal at
    https://data.ecb.europa.eu/data/data-categories/household-finance-and-consumption-survey

Waves and representative years (HFCS Network publications):
    wave 1 -> ~2010, wave 2 -> ~2014, wave 3 -> ~2017, wave 4 -> ~2021

Why a local CSV instead of the ECB SDW REST API
-----------------------------------------------

The ECB SDMX REST endpoint
``https://data-api.ecb.europa.eu/service/data/HFCN/{key}`` is robust
for known keys, but the HFCN dataflow has a ten-plus-dimension key
structure whose codelists vary by indicator. Rather than hard-code
brittle dimension strings up front, this module reads a tidy CSV
that the user produces once from the ECB Data Portal's per-series
CSV download. The schema is small and documented below; an SDW
fetcher can be layered in later without changing the harmonizer.

Expected CSV schema
-------------------

Path: ``data/raw/hfcs/hfcs_indicators.csv`` (override via
``WGA_HFCS_LOCAL``). One row per ``(country, wave)``. The first three
columns are required; all metric columns are optional but at least
one must be non-null per row.

    country               ISO 3166-1 alpha-2 (e.g. "DE", "FR")
    wave                  Integer: 1, 2, 3, or 4
    year                  Representative collection year for the wave
    gini                  Gini of net wealth, on [0, 1]
    mean_net_wealth       In current EUR
    median_net_wealth     In current EUR
    neg_wealth_share      Share of households with negative net wealth
    top10_share           Wealth share held by the top 10% of households
    top5_share            Wealth share held by the top 5% of households
    top1_share            Wealth share held by the top 1% of households

Delimiter: comma OR semicolon (auto-detected).
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import pandas as pd

log = logging.getLogger(__name__)


REQUIRED_COLS = {"country", "wave", "year"}
METRIC_COLS = [
    "gini", "mean_net_wealth", "median_net_wealth",
    "neg_wealth_share", "top10_share", "top5_share", "top1_share",
]
DEFAULT_LOCAL_PATH = "data/raw/hfcs/hfcs_indicators.csv"


def _resolve_path(explicit: Path | str | None) -> Path:
    if explicit is not None:
        return Path(explicit)
    env = os.environ.get("WGA_HFCS_LOCAL")
    if env:
        return Path(env)
    # Repository default
    here = Path(__file__).resolve().parents[2]
    return here / DEFAULT_LOCAL_PATH


def fetch(*_args, **_kwargs) -> Path:
    """No-op for HFCS: data must be downloaded manually from ECB.

    Returns the resolved path of the CSV the parser will read.
    The CLI prints a helpful instruction if the file is missing.
    """
    p = _resolve_path(None)
    if not p.exists():
        raise FileNotFoundError(
            f"HFCS source file not found at {p}.\n"
            "Download HFCS distributional indicators from "
            "https://data.ecb.europa.eu/data/data-categories/"
            "household-finance-and-consumption-survey, "
            "convert to the CSV schema documented in "
            "wealth_gini_atlas/ingest/hfcs.py, and place at this path "
            "(or set WGA_HFCS_LOCAL to point elsewhere)."
        )
    return p


def parse(path: Path | str | None = None) -> pd.DataFrame:
    """Read the HFCS CSV into a tidy frame keyed by (country, wave, year)."""
    p = _resolve_path(path)
    if not p.exists():
        raise FileNotFoundError(
            f"HFCS source file not found at {p}. See ingest/hfcs.py docstring."
        )

    # Auto-detect delimiter (comma vs semicolon).
    with open(p, "r", encoding="utf-8-sig") as f:
        head = f.readline()
    sep = ";" if head.count(";") > head.count(",") else ","

    df = pd.read_csv(p, sep=sep, dtype={"country": "string"})
    df.columns = [c.strip().lower() for c in df.columns]

    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        raise ValueError(f"HFCS CSV is missing required columns: {sorted(missing)}")

    df["country"] = df["country"].str.upper().str.strip()
    df["wave"] = pd.to_numeric(df["wave"], errors="coerce").astype("Int8")
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int32")
    for c in METRIC_COLS:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("Float64")
        else:
            df[c] = pd.Series([pd.NA] * len(df), dtype="Float64")

    # Drop rows lacking the natural key
    df = df.dropna(subset=["country", "wave", "year"]).reset_index(drop=True)

    # Drop rows with no metric values at all
    present_any = df[METRIC_COLS].notna().any(axis=1)
    df = df[present_any].reset_index(drop=True)

    log.info("HFCS: %d rows across %d countries, waves %s",
             len(df), df["country"].nunique(),
             sorted(df["wave"].dropna().unique().tolist()))
    return df
