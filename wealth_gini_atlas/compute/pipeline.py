"""End-to-end pipeline: ingest -> harmonize -> Gini Atlas + Moments Atlas.

The pipeline produces TWO sibling release tables on every build:

* The headline **Wealth Gini Atlas** -- one row per
  (geo_id, year, wealth_concept, unit_of_analysis, source_dataset)
  with a non-null ``wealth_gini``.
* The companion **Wealth Moments Atlas** -- same schema with a
  nullable Gini, covering rows where the source publishes
  distributional moments (mean, median, top shares, negative
  share) but no headline Gini.

Sources contributing to each table

  WID  -> Gini Atlas (country-years with ``ghwealj/f/i992``)
        plus Moments Atlas (country-years with only shares / mean)
  HFCS -> Gini Atlas only (HFCS J4 publishes Gini for every wave)
  SCF  -> Moments Atlas only (no published Gini in chartbook)
  DFA  -> Moments Atlas only (4-bucket percentile shares)
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from ..harmonize import national as harm
from ..ingest import hfcs as hfcs_ingest
from ..ingest import wid as wid_ingest
from ..schema import empty_frame, validate

log = logging.getLogger(__name__)


def _build_wid_all(raw_dir: Path | None) -> pd.DataFrame:
    """Return the full harmonized WID frame (both Gini and moments rows)."""
    log.info("Parsing WID files")
    try:
        wid_wide = wid_ingest.parse(raw_dir=raw_dir)
    except FileNotFoundError as exc:
        log.warning("WID source not available, skipping: %s", exc)
        return empty_frame()
    log.info("Read %d WID country-year observations", len(wid_wide))

    # harm.from_wid currently drops null-Gini rows. Re-implement here at
    # pipeline level by calling the same harmonizer logic but keeping
    # all rows (Gini-or-moment). The cleanest way: temporarily strip
    # the null-Gini dropper inside a helper.
    from ..harmonize.national import _coerce, _headline_gini, _notes, _unit_of_analysis
    from ..schema import conform, empty_frame as _ef
    from .. import METHOD_VERSION
    from ..harmonize.iso import to_iso3

    if wid_wide.empty:
        return _ef()

    rows = []
    for _, r in wid_wide.iterrows():
        iso = to_iso3(r["country"])
        if iso is None:
            continue
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
            "negative_wealth_share": pd.NA,
            "mean_net_wealth": _coerce(r.get("mean_net_wealth")),
            "median_net_wealth": _coerce(r.get("median_net_wealth")),
            "top10_wealth_share": _coerce(r.get("top10_wealth_share")),
            "top1_wealth_share": _coerce(r.get("top1_wealth_share")),
            "bottom50_wealth_share": _coerce(r.get("bottom50_wealth_share")),
            "unit_of_analysis": _unit_of_analysis(r.get("gini_var")),
            "equivalence_scale": "none",
            "currency": "EUR_PPP",
            "source_dataset": "WID",
            "source_priority": "tier1",
            "comparability_tier": "B",
            "observed_vs_modeled": "imported",
            "top_tail_flag": "mixed",
            "method_version": METHOD_VERSION,
            "notes": notes,
        })

    df = pd.DataFrame(rows)
    df = df.dropna(subset=["year"])
    df = df.drop_duplicates(subset=["geo_id", "year", "wealth_concept",
                                    "unit_of_analysis", "source_dataset"])
    return conform(df)


def _build_hfcs() -> pd.DataFrame:
    log.info("Parsing HFCS file")
    try:
        hfcs_long = hfcs_ingest.parse()
    except FileNotFoundError as exc:
        log.info("HFCS source not available, skipping: %s", exc)
        return empty_frame()
    df = harm.from_hfcs(hfcs_long)
    log.info("HFCS release rows: %d", len(df))
    return df


def _build_oecd() -> pd.DataFrame:
    """OECD Wealth Distribution rows for the Gini Atlas."""
    from ..ingest import oecd as oecd_ingest
    try:
        df = oecd_ingest.harmonize_frame()
        log.info("OECD Gini Atlas rows: %d", len(df))
        return df
    except FileNotFoundError as exc:
        log.info("OECD source not available, skipping: %s", exc)
        return empty_frame()


def _build_lws() -> pd.DataFrame:
    """LWS microdata-based Gini rows for the Gini Atlas."""
    from ..ingest import lws as lws_ingest
    try:
        df = lws_ingest.harmonize_frame()
        log.info("LWS Gini Atlas rows: %d", len(df))
        return df
    except FileNotFoundError as exc:
        log.info("LWS source not available, skipping: %s", exc)
        return empty_frame()


def _build_scf_dfa() -> pd.DataFrame:
    """SCF + DFA rows for the Moments Atlas (US household moments)."""
    from ..ingest import dfa as dfa_ingest
    from ..ingest import scf as scf_ingest

    try:
        scf_df = scf_ingest.harmonize_frame()
        log.info("SCF moments rows: %d", len(scf_df))
    except FileNotFoundError as exc:
        log.info("SCF source not available, skipping: %s", exc)
        scf_df = empty_frame()

    try:
        dfa_df = dfa_ingest.harmonize_frame()
        log.info("DFA moments rows: %d", len(dfa_df))
    except FileNotFoundError as exc:
        log.info("DFA source not available, skipping: %s", exc)
        dfa_df = empty_frame()

    parts = [d for d in (scf_df, dfa_df) if not d.empty]
    if not parts:
        return empty_frame()
    return pd.concat(parts, ignore_index=True)


def build_release(raw_dir: Path | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build both the Gini Atlas and the Moments Atlas in one pass.

    Returns (gini_atlas_df, moments_atlas_df).
    """
    # --- Gather all WID rows (both Gini-bearing and moments-only) ---
    wid_all = _build_wid_all(raw_dir)
    wid_gini, wid_moments = harm.split_gini_and_moments(wid_all)
    log.info("WID rows: %d with Gini, %d moments-only", len(wid_gini), len(wid_moments))

    # HFCS, OECD, LWS -> Gini Atlas only.
    hfcs_df = _build_hfcs()
    oecd_df = _build_oecd()
    lws_df  = _build_lws()

    # SCF + DFA -> Moments Atlas only.
    sd_df = _build_scf_dfa()

    gini_parts    = [p for p in (wid_gini, hfcs_df, oecd_df, lws_df) if not p.empty]
    moments_parts = [p for p in (wid_moments, sd_df) if not p.empty]

    gini_atlas = (pd.concat(gini_parts, ignore_index=True).drop_duplicates(
        subset=["geo_id", "year", "wealth_concept", "unit_of_analysis",
                "source_dataset"]) if gini_parts else empty_frame())
    moments_atlas = (pd.concat(moments_parts, ignore_index=True).drop_duplicates(
        subset=["geo_id", "year", "wealth_concept", "unit_of_analysis",
                "source_dataset"]) if moments_parts else empty_frame())

    if not gini_atlas.empty:
        log.info(
            "Gini Atlas: %d rows, %d countries, %d sources, years %s..%s",
            len(gini_atlas), gini_atlas["geo_id"].nunique(),
            gini_atlas["source_dataset"].nunique(),
            int(gini_atlas["year"].min()), int(gini_atlas["year"].max()),
        )
    if not moments_atlas.empty:
        log.info(
            "Moments Atlas: %d rows, %d countries, %d sources, years %s..%s",
            len(moments_atlas), moments_atlas["geo_id"].nunique(),
            moments_atlas["source_dataset"].nunique(),
            int(moments_atlas["year"].min()), int(moments_atlas["year"].max()),
        )

    if not gini_atlas.empty:
        issues = validate(gini_atlas, strict=False, mode="gini_atlas")
        for i in issues:
            log.warning("Gini Atlas validation: %s", i)
    if not moments_atlas.empty:
        issues = validate(moments_atlas, strict=False, mode="moments_atlas")
        for i in issues:
            log.warning("Moments Atlas validation: %s", i)

    return gini_atlas, moments_atlas
