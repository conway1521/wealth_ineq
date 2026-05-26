"""Harmonize source-specific national frames into the release schema."""

from __future__ import annotations

import pandas as pd

from .. import METHOD_VERSION
from ..schema import conform
from .iso import to_iso3


def from_wid(wid_wide: pd.DataFrame) -> pd.DataFrame:
    """Map the WID parse() output to the release schema (per-adult basis).

    The headline `wealth_gini` is the WID-published Gini. WID computes
    its Gini after their own treatment of negative wealth at the
    micro level, so we report it as the headline. We additionally
    keep it in `wealth_gini_raw` for transparency.
    """
    if wid_wide.empty:
        from ..schema import empty_frame
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
            "unit_of_analysis": "per_adult_equal_split",
            "equivalence_scale": "none",
            "currency": "EUR_PPP",   # WID standard reference unit for wealth levels
            "source_dataset": "WID",
            "source_priority": "tier1",
            "comparability_tier": "B",
            "observed_vs_modeled": "imported",
            "top_tail_flag": "mixed",   # WID uses admin+survey blends per country
            "method_version": METHOD_VERSION,
            "notes": "Imported from World Inequality Database bulk download.",
        })

    df = pd.DataFrame(rows)
    df = df.dropna(subset=["year", "wealth_gini"], how="all")
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
