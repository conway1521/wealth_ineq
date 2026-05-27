"""OECD Wealth Distribution Database ingest.

The OECD compiles Gini coefficients and distributional moments for net
household wealth from national household surveys across OECD member
states. For European countries it largely draws from HFCS; for
non-HFCS countries (Australia, Canada, Japan, Korea, UK, US, etc.) it
is the main internationally comparable source.

Source file
-----------
Dataset ID: WEALTH (OECD.Stat "Wealth Distribution" dataset)

Auto-fetch (requires outbound HTTPS to stats.oecd.org):
    wga fetch oecd

Manual download (if network is restricted):
    1. Go to https://stats.oecd.org/Index.aspx?DataSetCode=WEALTH
    2. "Export" → "Text file (CSV)" → enable "Full data extract"
    3. Save to data/raw/oecd/WEALTH.csv

Expected CSV structure (OECD SDMX-CSV layout)::

    MEASURE,COUNTRY,TIME_PERIOD,OBS_VALUE,UNIT_MEASURE,...
    GINI_NW,AUS,2018,0.621,...
    SHARE_TOP10_NW,AUS,2018,0.572,...
    MEAN_NW,AUS,2018,273400,...
    ...

Measure codes (we consume)::

    GINI_NW          Gini for household net wealth (0-1 scale)
    SHARE_TOP10_NW   Top-10% wealth share (0-1 scale)
    SHARE_TOP1_NW    Top-1% wealth share (0-1, where published)
    SHARE_BOT50_NW   Bottom-50% wealth share (0-1, where published)
    MEAN_NW          Mean household net wealth (PPP USD 2015)
    MED_NW           Median household net wealth (PPP USD 2015)

Note: not all measures are available for all country-years; the
parser tolerates missing columns gracefully.

Harmonization contract
----------------------
* ``source_dataset    = "OECD"``
* ``source_priority   = "tier2"`` (prefer WID tier1 / HFCS tier1 when
  they overlap; OECD is the preferred source for non-HFCS non-WID
  OECD countries such as AU, CA, JP, KR, GB, NZ).
* ``comparability_tier = "B"`` (OECD compiles from heterogeneous
  national surveys; not as harmonized as HFCS).
* ``unit_of_analysis  = "household"``
* ``top_tail_flag     = "survey_only"`` (OECD draws from survey data;
  some country series may be partially admin-enhanced -- see notes).
* ``currency          = "USD_PPP_2015"`` (OECD PPP-adjusted 2015 USD
  for mean/median; Gini and shares are dimensionless).
"""

from __future__ import annotations

import io
import logging
import os
from pathlib import Path

import pandas as pd
import requests

from .. import METHOD_VERSION
from ..harmonize.iso import to_iso3
from ..schema import conform, empty_frame

log = logging.getLogger(__name__)

DEFAULT_RAW_DIR = "data/raw/oecd"

# OECD SDMX-CSV API endpoint for the Wealth Distribution dataset
_OECD_API_URL = (
    "https://stats.oecd.org/sdmx-json/data/WEALTH/all/all"
    "?contentType=csv&detail=DataOnly"
)

# Fallback: direct OECD.Stat bulk CSV download
_OECD_BULK_URL = (
    "https://stats.oecd.org/SDMX-JSON/data/WEALTH/all/all"
    "?contentType=csv"
)

# Measure codes we want -> our column names
_MEASURE_MAP = {
    "GINI_NW":         "wealth_gini",
    "SHARE_TOP10_NW":  "top10_wealth_share",
    "SHARE_TOP1_NW":   "top1_wealth_share",
    "SHARE_BOT50_NW":  "bottom50_wealth_share",
    "MEAN_NW":         "mean_net_wealth",
    "MED_NW":          "median_net_wealth",
}

# Some OECD releases use alternative measure codes
_MEASURE_ALIASES = {
    "GINI":            "wealth_gini",
    "P90_SHARE":       "top10_wealth_share",
    "P99_SHARE":       "top1_wealth_share",
    "BOTTOM50_SHARE":  "bottom50_wealth_share",
    "MEAN":            "mean_net_wealth",
    "MEDIAN":          "median_net_wealth",
}


def _resolve_raw_dir() -> Path:
    env = os.environ.get("WGA_OECD_LOCAL")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[2] / DEFAULT_RAW_DIR


def fetch(timeout: int = 120) -> Path:
    """Download the OECD Wealth dataset into data/raw/oecd/.

    Tries the SDMX-JSON CSV endpoint; if that fails, tries the
    legacy OECD.Stat bulk URL.  Falls back gracefully to local files
    if network is restricted (set WGA_OECD_LOCAL to override path).
    """
    local = os.environ.get("WGA_OECD_LOCAL")
    if local:
        p = Path(local)
        if not p.is_dir():
            raise FileNotFoundError(f"WGA_OECD_LOCAL={local} is not a directory")
        log.info("Using local OECD mirror at %s", p)
        return p

    raw = _resolve_raw_dir()
    raw.mkdir(parents=True, exist_ok=True)
    out = raw / "WEALTH.csv"

    for url in (_OECD_API_URL, _OECD_BULK_URL):
        try:
            log.info("Fetching OECD Wealth dataset from %s", url)
            r = requests.get(url, timeout=timeout)
            r.raise_for_status()
            out.write_bytes(r.content)
            log.info("Saved %d bytes -> %s", len(r.content), out)
            return raw
        except requests.RequestException as exc:
            log.warning("OECD fetch failed (%s): %s", url, exc)

    raise FileNotFoundError(
        f"Could not download OECD Wealth dataset automatically.\n"
        "Manual download:\n"
        "  1. Go to https://stats.oecd.org/Index.aspx?DataSetCode=WEALTH\n"
        "  2. Export -> Text file (CSV) -> Full data extract\n"
        f"  3. Save to {out}"
    )


def _detect_and_load(path: Path) -> pd.DataFrame:
    """Read OECD CSV regardless of whether it uses the SDMX-JSON or
    legacy OECD.Stat column layout.  Returns a normalized frame with
    columns: country_code, year, measure, value.
    """
    df = pd.read_csv(path, low_memory=False)
    cols_lower = {c.lower(): c for c in df.columns}

    # --- SDMX-JSON layout: MEASURE, COUNTRY / LOCATION, TIME_PERIOD, OBS_VALUE ---
    measure_col = (cols_lower.get("measure")
                   or cols_lower.get("subject")
                   or cols_lower.get("variable"))
    country_col = (cols_lower.get("country")
                   or cols_lower.get("location")
                   or cols_lower.get("cou"))
    time_col    = (cols_lower.get("time_period")
                   or cols_lower.get("time")
                   or cols_lower.get("year"))
    value_col   = (cols_lower.get("obs_value")
                   or cols_lower.get("value"))

    if all(c is not None for c in (measure_col, country_col, time_col, value_col)):
        out = df[[measure_col, country_col, time_col, value_col]].copy()
        out.columns = ["measure", "country_code", "year", "value"]
        return out

    raise ValueError(
        f"Cannot parse OECD CSV at {path}.\n"
        f"Columns found: {list(df.columns)}\n"
        "Expected at minimum: a measure column, a country column, "
        "a time column, and a value column."
    )


def parse(raw_dir: Path | None = None) -> pd.DataFrame:
    """Parse the OECD Wealth CSV into a tidy wide frame.

    Returns columns: country_code, year, wealth_gini, top10_wealth_share,
    top1_wealth_share, bottom50_wealth_share, mean_net_wealth,
    median_net_wealth.  All optional except country_code and year.
    """
    raw = Path(raw_dir) if raw_dir else _resolve_raw_dir()
    csv_files = sorted(raw.glob("WEALTH*.csv"))
    if not csv_files:
        raise FileNotFoundError(
            f"No WEALTH*.csv files found under {raw}. "
            "Run `wga fetch oecd` or set WGA_OECD_LOCAL."
        )

    long = _detect_and_load(csv_files[0])
    long["value"] = pd.to_numeric(long["value"], errors="coerce")
    long["year"]  = pd.to_numeric(long["year"],  errors="coerce")
    long = long.dropna(subset=["value", "year"])
    long["year"] = long["year"].astype(int)

    # Normalize measure codes (try primary map, then aliases)
    full_map = {**_MEASURE_MAP, **_MEASURE_ALIASES}
    long["measure_norm"] = long["measure"].map(full_map)
    long = long[long["measure_norm"].notna()]

    if long.empty:
        log.warning("OECD CSV had no recognized measure codes. "
                    "Known codes: %s", sorted(full_map.keys()))
        return pd.DataFrame()

    # Pivot: one row per (country, year), measures as columns
    wide = (long.pivot_table(index=["country_code", "year"],
                             columns="measure_norm",
                             values="value",
                             aggfunc="first")
               .reset_index())
    wide.columns.name = None
    log.info("OECD Wealth: %d country-year observations, %d countries",
             len(wide), wide["country_code"].nunique())
    return wide


def harmonize_frame(raw_dir: Path | None = None) -> pd.DataFrame:
    """Return OECD rows ready for the Gini Atlas (release schema)."""
    raw = Path(raw_dir) if raw_dir else _resolve_raw_dir()
    if not any(raw.glob("WEALTH*.csv")):
        raise FileNotFoundError(
            f"No WEALTH*.csv found under {raw}. Run `wga fetch oecd`."
        )

    wide = parse(raw_dir)
    if wide.empty:
        return empty_frame()

    rows = []
    for _, r in wide.iterrows():
        iso = to_iso3(str(r["country_code"]))
        if iso is None:
            continue
        iso3, name = iso

        gini = r.get("wealth_gini")
        if pd.isna(gini):
            continue                   # OECD rows without a Gini -> Moments Atlas

        # OECD Ginis are sometimes expressed as 0–100; rescale if needed
        if not pd.isna(gini) and gini > 1.0:
            gini = gini / 100.0

        rows.append({
            "geo_id": iso3,
            "geo_name": name,
            "geo_level": "country",
            "year": int(r["year"]),
            "wealth_concept": "net_wealth",
            "wealth_gini": gini,
            "wealth_gini_raw": gini,
            "negative_wealth_share": pd.NA,
            "mean_net_wealth":      r.get("mean_net_wealth"),
            "median_net_wealth":    r.get("median_net_wealth"),
            "top10_wealth_share":   r.get("top10_wealth_share"),
            "top1_wealth_share":    r.get("top1_wealth_share"),
            "bottom50_wealth_share": r.get("bottom50_wealth_share"),
            "unit_of_analysis": "household",
            "equivalence_scale": "none",
            "currency": "USD_PPP_2015",
            "source_dataset": "OECD",
            "source_priority": "tier2",
            "comparability_tier": "B",
            "observed_vs_modeled": "imported",
            "top_tail_flag": "survey_only",
            "method_version": METHOD_VERSION,
            "notes": "OECD Wealth Distribution Database (WEALTH dataset).",
        })

    df = pd.DataFrame(rows).dropna(subset=["year"])
    log.info("OECD Gini Atlas rows: %d (%d countries)",
             len(df), df["geo_id"].nunique() if not df.empty else 0)
    return conform(df)
