"""Luxembourg Wealth Study (LWS) ingest -- v0.4 scaffold.

LWS is part of the LIS Data Center and provides internationally
harmonized microdata-based wealth statistics for ~25 countries,
including the US household-basis Gini that WID's equal-split series
cannot produce.  LWS Ginis are the gold-standard cross-country
benchmark for the Gini Atlas.

Access paths (choose one)
--------------------------

**Path A -- ReShare (easiest for Gini time series):**
  The UK Data Service ReShare archive hosts a precomputed Gini series:
  "Luxembourg Wealth Study Database: Gini Inequality Coefficients,
  1993-2020" at https://reshare.ukdataservice.ac.uk/855655/
  Requires a free UK Data Service account (no institutional affiliation
  needed). Download ``lws-gini-coefficients.csv`` and place it in
  ``data/raw/lws/``.

**Path B -- LIS LISSY (full microdata):**
  Register at https://www.lisdatacenter.org/data-access/lissy/ (free
  for non-commercial research, 2-3 day approval). Submit a LISSY job
  to compute Ginis, top-shares, means, and medians across all LWS
  datasets. Expected output format documented below.

**Path C -- LIS DART (manual extraction):**
  The DART visualization tool at https://dart.lisdatacenter.org/
  requires no registration. You can extract wealth Ginis country by
  country, but there is no bulk CSV export -- not recommended for
  pipeline use.

Countries in LWS (as of 2024)
------------------------------
AT, AU, CA, CL, CY, DE, FI, GR, HU, IS, IT, JP, KR, LT, LU, NO,
PL, PT, SE, SK, SI, ES, GB, US (24 countries, varies by wave).

Waves are country-specific; roughly decadal, covering 1993–2020.

Expected file layout (Path A -- ReShare CSV)
--------------------------------------------

Columns::

    country_code, year, wave, gini_nw, gini_nw_se,
    [optional: top10_nw, median_nw, mean_nw]

Example row::

    US, 2019, lws2019us, 0.872, 0.003, 0.738, 68000, 175000

Expected file layout (Path B -- LISSY output)
----------------------------------------------

If you run a custom LISSY job, produce a CSV with at minimum::

    iso3, year, wave_name, gini_nw, top10_nw, top1_nw,
    median_nw, mean_nw, currency

Harmonization contract
----------------------
* ``source_dataset    = "LWS"``
* ``source_priority   = "tier1"`` (microdata-based; highest quality)
* ``comparability_tier = "A"`` (internationally harmonized definition)
* ``unit_of_analysis  = "household"``
* ``top_tail_flag     = "survey_only"``
* ``currency``        = depends on LISSY output (commonly USD PPP 2017)

Implementation status
---------------------
Scaffold.  ``harmonize_frame()`` raises ``FileNotFoundError`` if no
LWS source file is present.  Once you drop a CSV under
``data/raw/lws/``, run ``wga build`` and this module will be invoked
automatically.  The parser below handles the ReShare format; for
custom LISSY output, add your column names to ``_COL_MAP``.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import pandas as pd

from .. import METHOD_VERSION
from ..harmonize.iso import to_iso3
from ..schema import conform, empty_frame

log = logging.getLogger(__name__)

DEFAULT_RAW_DIR = "data/raw/lws"

# Map possible input column names -> our internal names
_COL_MAP = {
    # Gini
    "gini_nw": "wealth_gini", "gini": "wealth_gini",
    "gini_net_worth": "wealth_gini", "gini_wealth": "wealth_gini",
    # Top-10 share
    "top10_nw": "top10_wealth_share", "top10": "top10_wealth_share",
    "share_top10": "top10_wealth_share", "p90_share": "top10_wealth_share",
    # Top-1 share
    "top1_nw": "top1_wealth_share", "top1": "top1_wealth_share",
    "share_top1": "top1_wealth_share", "p99_share": "top1_wealth_share",
    # Bottom-50 share
    "bot50_nw": "bottom50_wealth_share", "bottom50": "bottom50_wealth_share",
    "share_bot50": "bottom50_wealth_share",
    # Mean / median
    "mean_nw": "mean_net_wealth", "mean": "mean_net_wealth",
    "median_nw": "median_net_wealth", "median": "median_net_wealth",
    # Country
    "country_code": "country_code", "iso3": "country_code",
    "iso2": "country_code", "country": "country_code",
    "cntry": "country_code",
    # Year
    "year": "year", "survey_year": "year", "ref_year": "year",
}


def _resolve_raw_dir() -> Path:
    env = os.environ.get("WGA_LWS_LOCAL")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[2] / DEFAULT_RAW_DIR


def fetch() -> Path:
    raw = _resolve_raw_dir()
    if any(raw.glob("*.csv")) or any(raw.glob("*.xlsx")) or any(raw.glob("*.dta")):
        return raw
    raise FileNotFoundError(
        f"No LWS source files found under {raw}.\n\n"
        "Quickest path (no institutional affiliation needed):\n"
        "  1. Create a free UK Data Service account at "
        "https://ukdataservice.ac.uk/\n"
        "  2. Download the ReShare dataset at "
        "https://reshare.ukdataservice.ac.uk/855655/\n"
        "     (LWS Gini Inequality Coefficients 1993-2020)\n"
        f"  3. Place the .dta (or .csv / .xlsx) file in {raw}/\n\n"
        "Alternatively, register for LISSY at "
        "https://www.lisdatacenter.org/data-access/lissy/ "
        "and see the module docstring for the expected LISSY output format."
    )


def parse(raw_dir: Path | None = None) -> pd.DataFrame:
    """Parse the LWS source file into a normalized frame.

    Returns columns: country_code, year, wealth_gini,
    top10_wealth_share, top1_wealth_share, bottom50_wealth_share,
    mean_net_wealth, median_net_wealth.  Only country_code, year, and
    wealth_gini are required; all others are optional.
    """
    raw = Path(raw_dir) if raw_dir else _resolve_raw_dir()
    files = (sorted(raw.glob("*.csv"))
             + sorted(raw.glob("*.xlsx"))
             + sorted(raw.glob("*.dta")))
    if not files:
        raise FileNotFoundError(f"No CSV/XLSX/DTA found under {raw}")

    src = files[0]
    log.info("LWS source file: %s", src.name)
    if src.suffix == ".xlsx":
        df = pd.read_excel(src)
    elif src.suffix == ".dta":
        df = pd.read_stata(src, convert_categoricals=False)
    else:
        df = pd.read_csv(src, low_memory=False)

    # Normalize column names
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    rename = {c: _COL_MAP[c] for c in df.columns if c in _COL_MAP}
    df = df.rename(columns=rename)

    required = {"country_code", "year", "wealth_gini"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"LWS file {src} is missing required columns: {missing}.\n"
            f"Columns present: {list(df.columns)}\n"
            "Add your column names to _COL_MAP in ingest/lws.py."
        )

    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["wealth_gini"] = pd.to_numeric(df["wealth_gini"], errors="coerce")
    df = df.dropna(subset=["country_code", "year", "wealth_gini"])
    df["year"] = df["year"].astype(int)

    # Rescale Gini if expressed as 0-100
    mask = df["wealth_gini"] > 1.0
    if mask.any():
        log.info("LWS: rescaling %d Gini values from 0-100 to 0-1", mask.sum())
        df.loc[mask, "wealth_gini"] = df.loc[mask, "wealth_gini"] / 100.0

    log.info("LWS parsed: %d rows, %d countries",
             len(df), df["country_code"].nunique())
    return df


def harmonize_frame(raw_dir: Path | None = None) -> pd.DataFrame:
    """Return LWS rows ready for the Gini Atlas (release schema)."""
    fetch()
    df = parse(raw_dir)
    if df.empty:
        return empty_frame()

    rows = []
    for _, r in df.iterrows():
        iso = to_iso3(str(r["country_code"]))
        if iso is None:
            log.debug("LWS: skipping unrecognized country code %r",
                      r["country_code"])
            continue
        iso3, name = iso

        rows.append({
            "geo_id": iso3,
            "geo_name": name,
            "geo_level": "country",
            "year": int(r["year"]),
            "wealth_concept": "net_wealth",
            "wealth_gini": float(r["wealth_gini"]),
            "wealth_gini_raw": float(r["wealth_gini"]),
            "negative_wealth_share": pd.NA,
            "mean_net_wealth":      r.get("mean_net_wealth"),
            "median_net_wealth":    r.get("median_net_wealth"),
            "top10_wealth_share":   r.get("top10_wealth_share"),
            "top1_wealth_share":    r.get("top1_wealth_share"),
            "bottom50_wealth_share": r.get("bottom50_wealth_share"),
            "unit_of_analysis": "household",
            "equivalence_scale": "none",
            "currency": "USD_PPP",
            "source_dataset": "LWS",
            "source_priority": "tier1",
            "comparability_tier": "A",
            "observed_vs_modeled": "imported",
            "top_tail_flag": "survey_only",
            "method_version": METHOD_VERSION,
            "notes": "LWS microdata-based Gini (internationally harmonized).",
        })

    result = pd.DataFrame(rows).dropna(subset=["year"])
    log.info("LWS Gini Atlas rows: %d (%d countries)",
             len(result), result["geo_id"].nunique() if not result.empty else 0)
    return conform(result)
