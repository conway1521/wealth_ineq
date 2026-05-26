"""Distributional Financial Accounts (DFA) ingest -- v0.3 scaffold.

The Federal Reserve Board's DFA splits the Financial Accounts of
the United States by wealth-percentile bucket at quarterly frequency.
The published buckets are:

    Top 1%, Next 9% (90th-99th), Next 40% (50th-90th), Bottom 50%

DFA does not publish a Gini coefficient. It can supply:

* Top 1% wealth share         (quarterly)
* Top 10% wealth share        (sum of top1 + next9)
* Bottom 50% wealth share     (quarterly)
* Mean wealth per percentile-bucket (level, USD)

DFA's appeal vs SCF: it is anchored to Financial Accounts aggregates
(``admin_enhanced`` top tail), it is quarterly rather than triennial,
and it stretches back to 1989Q3.

This module ingests DFA into the Moments Atlas only -- no Gini.

Source file we expect
---------------------

The DFA dataset is published as a single ZIP at

    https://www.federalreserve.gov/releases/efa/dataset/dfa.zip

which unpacks to ``dfa-networth-levels-detail.csv`` and a few
related files. Place either the ZIP or the unpacked CSV(s) under
``data/raw/dfa/``.

Harmonization contract
----------------------

* ``unit_of_analysis = "household"`` (DFA scales SCF micro to the
  Flow-of-Funds aggregates).
* ``equivalence_scale = "none"``.
* ``currency = "USD"``.
* ``source_dataset = "DFA"``.
* ``source_priority = "tier1"`` -- DFA is the canonical
  admin-enhanced US wealth-distribution series.
* ``comparability_tier = "B"`` (different concept boundaries than
  HFCS / SCF chartbook).
* ``top_tail_flag = "admin_enhanced"``.
* ``observed_vs_modeled = "imported"``.

Quarterly -> annual: we collapse to year-end (Q4) snapshots so each
geo-year-source row remains unique.

Implementation status
---------------------

Scaffold. ``harmonize_frame()`` raises ``FileNotFoundError`` if no
DFA source is on disk. Parser is filled in once a real file is
committed.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import pandas as pd

from .. import METHOD_VERSION
from ..schema import conform, empty_frame

log = logging.getLogger(__name__)


DEFAULT_RAW_DIR = "data/raw/dfa"


def _resolve_raw_dir() -> Path:
    env = os.environ.get("WGA_DFA_LOCAL")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[2] / DEFAULT_RAW_DIR


def fetch(*_args, **_kwargs) -> Path:
    raw = _resolve_raw_dir()
    if any(raw.glob("dfa*.csv")) or any(raw.glob("dfa*.zip")):
        return raw
    raise FileNotFoundError(
        f"No DFA source files found under {raw}.\n"
        "Expected: DFA dataset ZIP or unpacked CSV(s) from "
        "https://www.federalreserve.gov/releases/efa/dataset/dfa.zip\n"
        "See wealth_gini_atlas/ingest/dfa.py docstring for details."
    )


def parse(raw_dir: Path | None = None) -> pd.DataFrame:
    """Parse DFA source files into a tidy frame keyed by (year,).

    Returns columns: year, top1_share, top10_share, bottom50_share,
    mean_net_wealth (annualized to Q4).
    """
    raise NotImplementedError(
        "DFA parse() not yet implemented. Commit dfa.zip (or unpacked "
        "CSVs) to data/raw/dfa/ and the parser will be wired in "
        "against the real file structure."
    )


def harmonize_frame(raw_dir: Path | None = None) -> pd.DataFrame:
    """Return DFA rows ready for the Moments Atlas (release schema)."""
    fetch()
    df_long = parse(raw_dir)
    if df_long.empty:
        return empty_frame()

    rows = []
    for _, r in df_long.iterrows():
        rows.append({
            "geo_id": "USA",
            "geo_name": "United States",
            "geo_level": "country",
            "year": int(r["year"]) if pd.notna(r.get("year")) else pd.NA,
            "wealth_concept": "net_wealth",
            "wealth_gini": pd.NA,
            "wealth_gini_raw": pd.NA,
            "negative_wealth_share": pd.NA,
            "mean_net_wealth": r.get("mean_net_wealth"),
            "median_net_wealth": pd.NA,
            "top10_wealth_share": r.get("top10_share"),
            "top1_wealth_share":  r.get("top1_share"),
            "bottom50_wealth_share": r.get("bottom50_share"),
            "unit_of_analysis": "household",
            "equivalence_scale": "none",
            "currency": "USD",
            "source_dataset": "DFA",
            "source_priority": "tier1",
            "comparability_tier": "B",
            "observed_vs_modeled": "imported",
            "top_tail_flag": "admin_enhanced",
            "method_version": METHOD_VERSION,
            "notes": "Imported from DFA dataset.zip (Q4 annual snapshot).",
        })
    df = pd.DataFrame(rows).dropna(subset=["year"])
    return conform(df)
