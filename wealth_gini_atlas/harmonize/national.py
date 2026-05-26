"""Harmonize source-specific national frames into the release schema."""

from __future__ import annotations

import pandas as pd

from .. import METHOD_VERSION
from ..schema import conform, empty_frame
from .iso import to_iso3


# WID pop suffix -> release unit_of_analysis
_POP_TO_UNIT = {
    "j": "per_adult_equal_split",
    "i": "individual",
    "f": "per_adult",   # WID's "fiscal" / heads-of-household basis
}


def _pop_letter(varcode) -> str | None:
    """Extract the 7th character of a WID variable code."""
    if isinstance(varcode, str) and len(varcode) >= 7:
        return varcode[6]
    return None


def _unit_of_analysis(gini_var) -> str:
    pop = _pop_letter(gini_var)
    return _POP_TO_UNIT.get(pop, "per_adult_equal_split")


def _notes(row: pd.Series) -> str:
    """Build a notes string listing the WID variables used for each metric."""
    parts = []
    for col, label in (("gini_var", "G"),
                       ("mean_var", "mean"),
                       ("median_var", "med"),
                       ("top10_var", "top10"),
                       ("top1_var", "top1"),
                       ("bottom50_var", "bot50")):
        v = row.get(col)
        if isinstance(v, str) and v:
            parts.append(f"{label}={v}")
    if parts:
        return "WID vars: " + "; ".join(parts)
    return "WID import"


def from_wid(wid_wide: pd.DataFrame) -> pd.DataFrame:
    """Map the WID parse() output to the release schema."""
    if wid_wide.empty:
        return empty_frame()

    rows = []
    for _, r in wid_wide.iterrows():
        iso = to_iso3(r["country"])
        if iso is None:
            continue  # skip aggregates / unmapped codes
        iso3, name = iso

        rows.append({
            "geo_id": iso3,
            "geo_name": name,
            "geo_level": "country",
            "year": int(r["year"]) if pd.notna(r["year"]) else pd.NA,
            "wealth_concept": "net_wealth",
            "wealth_gini": _coerce(r.get("wealth_gini_raw_source")),
            "wealth_gini_raw": _coerce(r.get("wealth_gini_raw_source")),
            "negative_wealth_share": pd.NA,  # not published in WID series
            "mean_net_wealth": _coerce(r.get("mean_net_wealth")),
            "median_net_wealth": _coerce(r.get("median_net_wealth")),
            "top10_wealth_share": _coerce(r.get("top10_wealth_share")),
            "top1_wealth_share": _coerce(r.get("top1_wealth_share")),
            "bottom50_wealth_share": _coerce(r.get("bottom50_wealth_share")),
            "unit_of_analysis": _unit_of_analysis(r.get("gini_var")),
            "equivalence_scale": "none",
            "currency": "EUR_PPP",  # WID standard reference unit for wealth levels
            "source_dataset": "WID",
            "source_priority": "tier1",
            "comparability_tier": "B",
            "observed_vs_modeled": "imported",
            "top_tail_flag": "mixed",  # WID blends survey + admin per country
            "method_version": METHOD_VERSION,
            "notes": _notes(r),
        })

    df = pd.DataFrame(rows)
    # Drop rows that carry no signal whatsoever
    metric_cols = ["wealth_gini", "mean_net_wealth", "median_net_wealth",
                   "top10_wealth_share", "top1_wealth_share",
                   "bottom50_wealth_share"]
    df = df.dropna(subset=metric_cols, how="all")
    df = df.dropna(subset=["year"])
    df = df.drop_duplicates(subset=["geo_id", "year", "wealth_concept",
                                    "unit_of_analysis", "source_dataset"])
    return conform(df)


def _coerce(v):
    if v is None:
        return pd.NA
    try:
        if pd.isna(v):
            return pd.NA
    except (TypeError, ValueError):
        return pd.NA
    return float(v)
