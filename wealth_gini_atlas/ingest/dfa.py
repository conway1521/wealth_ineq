"""Distributional Financial Accounts (DFA) ingest.

Source file (Federal Reserve Board, US public domain):
  data/raw/dfa/dfa-networth-shares.csv

Download the full DFA dataset ZIP from
https://www.federalreserve.gov/releases/efa/dataset/dfa.zip
and unpack it under data/raw/dfa/.

DFA publishes quarterly wealth-share decompositions for five
net-worth percentile buckets:

  TopPt1          top 0.1 %     -> contributes to top_1%
  RemainingTop1   next 0.9 %    -> contributes to top_1%
  Next9           next 9 %      -> contributes to top_10%
  Next40          next 40 %     (50th-90th)
  Bottom50        bottom 50 %   -> bottom50_wealth_share

Mapping to release schema
-------------------------
  top1_share   = (TopPt1 + RemainingTop1) / 100
  top10_share  = (TopPt1 + RemainingTop1 + Next9) / 100
  bottom50     = Bottom50 / 100
  mean_net_wealth is not published per household; left null here --
    use the SCF source_dataset row for mean and median.

Quarterly -> annual: we collapse to Q4 snapshots (year-end) for a
unique (geo_id, year, source_dataset) key. DFA starts 1989Q3;
first Q4 is 1989Q4.

Unit of analysis: "household" (DFA scales SCF micro to Flow of Funds).
Currency: the shares are dimensionless; levels are not used here.
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


def fetch() -> Path:
    raw = _resolve_raw_dir()
    if (raw / "dfa-networth-shares.csv").exists():
        return raw
    raise FileNotFoundError(
        f"No DFA source files found under {raw}.\n"
        "Expected: dfa-networth-shares.csv from "
        "https://www.federalreserve.gov/releases/efa/dataset/dfa.zip"
    )


def parse(raw_dir: Path | None = None) -> pd.DataFrame:
    """Parse DFA networth-shares CSV into a tidy annual (Q4) frame.

    Returns columns: year, top1_share, top10_share, bottom50_share.
    """
    raw = Path(raw_dir) if raw_dir else _resolve_raw_dir()
    df = pd.read_csv(raw / "dfa-networth-shares.csv")

    # Keep Q4 only
    df = df[df["Date"].str.endswith("Q4")].copy()
    df["year"] = df["Date"].str[:4].astype(int)

    # Pivot: one row per (Date, year), categories become columns
    pivot = (df.pivot_table(index=["Date", "year"],
                            columns="Category",
                            values="Net worth",
                            aggfunc="first")
               .reset_index())

    # Shares are expressed as percentages in the source; divide by 100.
    rows = []
    for _, r in pivot.iterrows():
        top1 = (r.get("TopPt1", float("nan"))
                + r.get("RemainingTop1", float("nan"))) / 100
        top10 = (r.get("TopPt1", float("nan"))
                 + r.get("RemainingTop1", float("nan"))
                 + r.get("Next9", float("nan"))) / 100
        bot50 = r.get("Bottom50", float("nan")) / 100
        rows.append({
            "year": int(r["year"]),
            "top1_share": round(top1, 6),
            "top10_share": round(top10, 6),
            "bottom50_share": round(bot50, 6),
        })

    return pd.DataFrame(rows)


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
            "year": int(r["year"]),
            "wealth_concept": "net_wealth",
            "wealth_gini": pd.NA,
            "wealth_gini_raw": pd.NA,
            "negative_wealth_share": pd.NA,
            "mean_net_wealth":     pd.NA,
            "median_net_wealth":   pd.NA,
            "top10_wealth_share":  r["top10_share"],
            "top1_wealth_share":   r["top1_share"],
            "bottom50_wealth_share": r["bottom50_share"],
            "unit_of_analysis": "household",
            "equivalence_scale": "none",
            "currency": "USD",
            "source_dataset": "DFA",
            "source_priority": "tier1",
            "comparability_tier": "B",
            "observed_vs_modeled": "imported",
            "top_tail_flag": "admin_enhanced",
            "method_version": METHOD_VERSION,
            "notes": (
                "DFA dfa-networth-shares.csv; Q4 annual snapshot. "
                "top1 = TopPt1 + RemainingTop1; "
                "top10 adds Next9. Shares dimensionless (source in %). "
                "mean/median null -- use SCF source_dataset row."
            ),
        })

    return conform(pd.DataFrame(rows).dropna(subset=["year"]))
