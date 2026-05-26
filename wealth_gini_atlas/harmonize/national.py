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

        gini_raw = _coerce(r.get("wealth_gini_raw_source"))
        gini_headline, clipped_from = _headline_gini(gini_raw)

        notes = _notes(r)
        if clipped_from is not None:
            notes = f"{notes}; headline clipped from {clipped_from:.4f} to [0,1]"

        rows.append({
            "geo_id": iso3,
            "geo_name": name,
            "geo_level": "country",
            "year": int(r["year"]) if pd.notna(r["year"]) else pd.NA,
            "wealth_concept": "net_wealth",
            "wealth_gini": gini_headline,
            "wealth_gini_raw": gini_raw,
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
            "notes": notes,
        })

    df = pd.DataFrame(rows)
    df = df.dropna(subset=["year"])
    df = df.drop_duplicates(subset=["geo_id", "year", "wealth_concept",
                                    "unit_of_analysis", "source_dataset"])
    return conform(df)


def split_gini_and_moments(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split a harmonized frame into (gini_atlas, moments_atlas).

    Rows with a non-null ``wealth_gini`` become the Gini Atlas; rows
    with null Gini but at least one other distributional moment
    become the Moments Atlas. Rows with neither are dropped.
    """
    if df.empty:
        return df, df.iloc[0:0].copy()

    has_gini = df["wealth_gini"].notna()
    moment_cols = ["mean_net_wealth", "median_net_wealth",
                   "top10_wealth_share", "top1_wealth_share",
                   "bottom50_wealth_share", "negative_wealth_share"]
    has_moment = df[moment_cols].notna().any(axis=1)

    gini_atlas = df[has_gini].reset_index(drop=True)
    moments_atlas = df[~has_gini & has_moment].reset_index(drop=True)
    return gini_atlas, moments_atlas


def _coerce(v):
    if v is None:
        return pd.NA
    try:
        if pd.isna(v):
            return pd.NA
    except (TypeError, ValueError):
        return pd.NA
    return float(v)


def from_hfcs(hfcs_long: pd.DataFrame) -> pd.DataFrame:
    """Map the HFCS parse() output to the release schema.

    HFCS is the strongest harmonized European household-basis source,
    so rows are tagged ``unit_of_analysis = "household"``,
    ``source_dataset = "HFCS"``, ``source_priority = "tier1"``,
    ``comparability_tier = "A"`` (the HFCS instrument is explicitly
    harmonized across euro-area NCBs), and ``top_tail_flag =
    "survey_only"`` because HFCS does not use administrative tax
    microdata to reweight the upper tail.

    HFCS publishes Ginis in [0, 1] by design, so the clipping logic
    used for WID is not exercised here -- but we route through the
    same helper to preserve the audit trail (out-of-range values still
    populate ``wealth_gini_raw`` and are logged in ``notes``).
    """
    if hfcs_long.empty:
        return empty_frame()

    rows = []
    for _, r in hfcs_long.iterrows():
        iso = to_iso3(r["country"])
        if iso is None:
            continue
        iso3, name = iso

        gini_raw = _coerce(r.get("gini"))
        gini_headline, clipped_from = _headline_gini(gini_raw)

        notes = f"HFCS wave {int(r['wave'])}"
        if clipped_from is not None:
            notes = f"{notes}; headline clipped from {clipped_from:.4f} to [0,1]"

        rows.append({
            "geo_id": iso3,
            "geo_name": name,
            "geo_level": "country",
            "year": int(r["year"]) if pd.notna(r["year"]) else pd.NA,
            "wealth_concept": "net_wealth",
            "wealth_gini": gini_headline,
            "wealth_gini_raw": gini_raw,
            "negative_wealth_share": _coerce(r.get("neg_wealth_share")),
            "mean_net_wealth": _coerce(r.get("mean_net_wealth")),
            "median_net_wealth": _coerce(r.get("median_net_wealth")),
            "top10_wealth_share": _coerce(r.get("top10_share")),
            "top1_wealth_share": _coerce(r.get("top1_share")),
            "bottom50_wealth_share": pd.NA,   # HFCS does not publish this directly
            "unit_of_analysis": "household",
            "equivalence_scale": "none",
            "currency": "EUR",
            "source_dataset": "HFCS",
            "source_priority": "tier1",
            "comparability_tier": "A",
            "observed_vs_modeled": "imported",
            "top_tail_flag": "survey_only",
            "method_version": METHOD_VERSION,
            "notes": notes,
        })

    df = pd.DataFrame(rows)
    df = df.dropna(subset=["year"])
    # HFCS: keep the Gini-required filter at this stage; the moments
    # path is only relevant for sources where Gini is structurally
    # absent (SCF, DFA), which the pipeline handles via
    # split_gini_and_moments downstream.
    df = df.dropna(subset=["wealth_gini"])
    df = df.drop_duplicates(subset=["geo_id", "year", "wealth_concept",
                                    "unit_of_analysis", "source_dataset"])
    return conform(df)


def _headline_gini(gini_raw):
    """Return (headline_gini, clipped_from_value_or_None).

    Source-published Ginis are occasionally just outside [0, 1] -- WID's
    own micro-data treatment can leave residual negative-wealth pressure
    in highly unequal economies, producing Ginis slightly above 1.0
    (e.g. South Africa pre-2014). For the headline we clip to [0, 1] so
    downstream users get the familiar invariant; the unclipped source
    value lives in ``wealth_gini_raw`` and the clip is logged in
    ``notes``.

    Values that fall too far outside the unit interval (more than 0.10
    away) are treated as anomalies and dropped (returned as NA).
    """
    if gini_raw is pd.NA:
        return pd.NA, None
    try:
        v = float(gini_raw)
    except (TypeError, ValueError):
        return pd.NA, None
    if v < -0.10 or v > 1.10:
        return pd.NA, v  # treat as anomalous; raw column still records it
    if v < 0.0:
        return 0.0, v
    if v > 1.0:
        return 1.0, v
    return v, None
