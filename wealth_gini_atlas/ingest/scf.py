"""Survey of Consumer Finances (SCF) ingest.

Source files (Federal Reserve Board, US public domain):
  data/raw/scf/interactive_bulletin_charts_all_mean.csv
  data/raw/scf/interactive_bulletin_charts_all_median.csv
  data/raw/scf/interactive_bulletin_charts_nwcat_mean.csv

All three are tab-downloadable CSVs from the SCF interactive chartbook at
https://www.federalreserve.gov/econres/scfindex.htm. Values are in
thousands of constant 2022 USD.

What this produces for the Moments Atlas (per survey year):
  mean_net_wealth    <- all_mean[Category=="All families", Net_Worth] * 1000
  median_net_wealth  <- all_median[Category=="All families", Net_Worth] * 1000
  top10_wealth_share <- mean_nwcat["90-100"] * 0.10 / total_mean_wealth
  bottom50_share     <- (mean_nwcat["<25"]*0.25 + mean_nwcat["25-49.9"]*0.25) / total
  top1_wealth_share  <- null (use DFA for this; SCF chartbook buckets stop at top-10)

Population fractions by net-worth decile group are fixed in the SCF design:
  Less than 25   = 0.25
  25-49.9        = 0.25
  50-74.9        = 0.25
  75-89.9        = 0.15
  90-100         = 0.10

Unit of analysis: "household" (SCF primary economic unit).
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import pandas as pd

from .. import METHOD_VERSION
from ..schema import conform, empty_frame

log = logging.getLogger(__name__)

DEFAULT_RAW_DIR = "data/raw/scf"

_POP_FRAC = {
    "Less than 25": 0.25,
    "25-49.9": 0.25,
    "50-74.9": 0.25,
    "75-89.9": 0.15,
    "90-100": 0.10,
}


def _resolve_raw_dir() -> Path:
    env = os.environ.get("WGA_SCF_LOCAL")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[2] / DEFAULT_RAW_DIR


def fetch() -> Path:
    raw = _resolve_raw_dir()
    if any(raw.glob("interactive_bulletin_charts_all_mean.csv")):
        return raw
    raise FileNotFoundError(
        f"No SCF source files found under {raw}.\n"
        "Expected: interactive_bulletin_charts_all_mean.csv "
        "(and _median, _nwcat_mean) from the SCF interactive chartbook at "
        "https://www.federalreserve.gov/econres/scfindex.htm"
    )


def parse(raw_dir: Path | None = None) -> pd.DataFrame:
    """Parse SCF chartbook CSVs into a tidy per-year frame.

    Returns columns: year, mean_net_wealth, median_net_wealth,
    top10_share, bottom50_share.  Values are in USD (converted from
    the source's thousands of 2022 USD).
    """
    raw = Path(raw_dir) if raw_dir else _resolve_raw_dir()

    all_mean = pd.read_csv(raw / "interactive_bulletin_charts_all_mean.csv")
    all_med = pd.read_csv(raw / "interactive_bulletin_charts_all_median.csv")
    nwcat_mean = pd.read_csv(raw / "interactive_bulletin_charts_nwcat_mean.csv")

    # Aggregate row
    mean_agg = (all_mean[all_mean["Category"] == "All families"]
                .set_index("year")["Net_Worth"])
    med_agg = (all_med[all_med["Category"] == "All families"]
               .set_index("year")["Net_Worth"])

    rows = []
    for yr in sorted(mean_agg.index):
        yr_nwcat = nwcat_mean[nwcat_mean["year"] == yr].set_index("Category")["Net_Worth"]

        # Weighted total from nwcat means (cross-check vs all_mean)
        total_w = sum(yr_nwcat.get(cat, 0) * frac
                      for cat, frac in _POP_FRAC.items())
        if total_w <= 0:
            continue

        top10 = yr_nwcat.get("90-100", float("nan")) * 0.10 / total_w
        bot50 = (yr_nwcat.get("Less than 25", float("nan")) * 0.25
                 + yr_nwcat.get("25-49.9", float("nan")) * 0.25) / total_w

        rows.append({
            "year": yr,
            # Source units: thousands of 2022 USD -> convert to USD
            "mean_net_wealth":   mean_agg[yr] * 1_000,
            "median_net_wealth": med_agg.get(yr, float("nan")) * 1_000,
            "top10_share": round(top10, 6),
            "bottom50_share": round(bot50, 6),
        })

    return pd.DataFrame(rows)


def harmonize_frame(raw_dir: Path | None = None) -> pd.DataFrame:
    """Return SCF rows ready for the Moments Atlas (release schema)."""
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
            "mean_net_wealth":     r["mean_net_wealth"],
            "median_net_wealth":   r["median_net_wealth"],
            "top10_wealth_share":  r["top10_share"],
            "top1_wealth_share":   pd.NA,
            "bottom50_wealth_share": r["bottom50_share"],
            "unit_of_analysis": "household",
            "equivalence_scale": "none",
            "currency": "USD_2022",
            "source_dataset": "SCF",
            "source_priority": "tier1",
            "comparability_tier": "B",
            "observed_vs_modeled": "imported",
            "top_tail_flag": "survey_only",
            "method_version": METHOD_VERSION,
            "notes": (
                "SCF interactive chartbook; means/medians in 2022 USD. "
                "Top-10/bottom-50 shares derived from nwcat bucket means "
                "(pop fracs 25/25/25/15/10). No top-1% from chartbook; "
                "use DFA source_dataset row for top-1%."
            ),
        })

    return conform(pd.DataFrame(rows).dropna(subset=["year"]))
