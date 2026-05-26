"""World Inequality Database (WID) ingest for the v0.1 backbone.

WID publishes per-country bulk CSVs at
    https://wid.world/bulk_download/

Each file is named ``WID_data_<ISO2>.csv`` (semicolon-delimited) with
**seven** columns::

    country;variable;percentile;year;value;age;pop

* ``variable`` is the WID base code, e.g. ``ghwealj992`` (Gini of net
  personal wealth, equal-split adults).
* ``age`` is the population age band (we use ``992``, the adult band).
* ``pop`` is the population-treatment code:
    - ``j`` = equal-split adults (each adult attributed equal share of
             household wealth -- WID's headline cross-country basis)
    - ``i`` = individuals (no household-sharing)
    - ``f`` = "fiscal" / heads-of-household basis (used for the US wealth
             series in WID)

Variable structure
------------------

The 7-character WID variable codes split as::

    [type][concept][pop][age]
       g     hweal    j   992    -> Gini, household wealth, equal-split, adults
       s     hweal    f   992    -> share, household wealth, fiscal, adults
       a     hweal    j   992    -> average, household wealth, equal-split
       m     hweal    j   992    -> median, household wealth, equal-split

Pop choice
----------

Different country files publish different pop variants. We prefer
``j`` (equal-split adults), fall back to ``f`` (fiscal), then ``i``
(individuals), per metric, per country-year. The harmonizer carries
the chosen pop suffix into ``unit_of_analysis`` and ``notes`` so
downstream users can audit each row.

Network
-------

Some sandboxed environments do not allow outbound HTTPS to wid.world.
``fetch()`` therefore reads from a local mirror directory if one is set
via the ``WGA_WID_LOCAL`` environment variable. The expected layout is::

    $WGA_WID_LOCAL/WID_data_FR.csv
    $WGA_WID_LOCAL/WID_data_US.csv
    ...
"""

from __future__ import annotations

import io
import logging
import os
import zipfile
from pathlib import Path
from typing import Iterable

import pandas as pd
import requests

log = logging.getLogger(__name__)

WID_BULK_URL = "https://wid.world/bulk_download/wid_all_data.zip"

# Variable codes for net personal wealth at age == 992 (adult band),
# in preferred order. We take the first match per (country, year).
GINI_VARS_ORDERED   = ["ghwealj992", "ghwealf992", "ghweali992"]
SHARE_VARS_ORDERED  = ["shwealj992", "shwealf992", "shweali992"]
MEAN_VARS_ORDERED   = ["ahwealj992", "ahwealf992", "ahweali992"]
MEDIAN_VARS_ORDERED = ["mhwealj992", "mhwealf992", "mhweali992"]

ALL_VARS = set(GINI_VARS_ORDERED
               + SHARE_VARS_ORDERED
               + MEAN_VARS_ORDERED
               + MEDIAN_VARS_ORDERED)

# Percentile brackets we consume for shares
SHARE_BRACKETS = {
    "top10":    "p90p100",
    "top1":     "p99p100",
    "bottom50": "p0p50",
}


def _raw_dir(root: Path | None = None) -> Path:
    root = root or Path(__file__).resolve().parents[2] / "data" / "raw" / "wid"
    root.mkdir(parents=True, exist_ok=True)
    return root


def fetch(countries: Iterable[str] | None = None,
          root: Path | None = None,
          timeout: int = 600) -> Path:
    """Download WID bulk data into ``data/raw/wid/``.

    If ``WGA_WID_LOCAL`` is set, treat that directory as the source of
    truth and return its path (no network access).
    """
    local = os.environ.get("WGA_WID_LOCAL")
    if local:
        p = Path(local)
        if not p.is_dir():
            raise FileNotFoundError(f"WGA_WID_LOCAL={local} is not a directory")
        log.info("Using local WID mirror at %s", p)
        return p

    out = _raw_dir(root)
    log.info("Fetching WID bulk archive %s", WID_BULK_URL)
    r = requests.get(WID_BULK_URL, timeout=timeout, stream=True)
    r.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
        zf.extractall(out)
    return out


def _read_country_csv(path: Path) -> pd.DataFrame:
    """Read a WID per-country CSV. Returns only the columns we use."""
    df = pd.read_csv(
        path,
        sep=";",
        dtype={"country": "string", "variable": "string", "percentile": "string"},
        usecols=["country", "variable", "percentile", "year", "value"],
        low_memory=False,
    )
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int32")
    df["value"] = pd.to_numeric(df["value"], errors="coerce").astype("Float64")
    return df


def _pick_first_available(long: pd.DataFrame,
                          var_list: list[str],
                          percentile: str) -> pd.DataFrame:
    """For each (country, year), keep the value from the first variable in
    ``var_list`` that has data at ``percentile``.

    Returns a frame with columns: country, year, value, var_used.
    """
    pieces = []
    for prio, var in enumerate(var_list):
        sub = long[
            (long["variable"] == var)
            & (long["percentile"] == percentile)
            & long["value"].notna()
        ]
        if sub.empty:
            continue
        sub = sub[["country", "year", "value"]].copy()
        sub["var_used"] = var
        sub["_pri"] = prio
        pieces.append(sub)

    if not pieces:
        return pd.DataFrame(columns=["country", "year", "value", "var_used"])

    stacked = pd.concat(pieces, ignore_index=True)
    stacked = stacked.sort_values(["country", "year", "_pri"])
    stacked = stacked.drop_duplicates(["country", "year"], keep="first")
    return stacked[["country", "year", "value", "var_used"]].reset_index(drop=True)


def parse(raw_dir: Path | None = None) -> pd.DataFrame:
    """Return a tidy wide frame keyed by (country, year).

    Columns:
        country, year,
        wealth_gini_raw_source, gini_var,
        mean_net_wealth,        mean_var,
        median_net_wealth,      median_var,
        top10_wealth_share,     top10_var,
        top1_wealth_share,      top1_var,
        bottom50_wealth_share,  bottom50_var.
    """
    raw_dir = Path(raw_dir) if raw_dir else _raw_dir()
    local = os.environ.get("WGA_WID_LOCAL")
    if local:
        raw_dir = Path(local)

    files = sorted(raw_dir.glob("WID_data_*.csv"))
    if not files:
        raise FileNotFoundError(
            f"No WID_data_*.csv files found in {raw_dir}. "
            "Run `wga fetch wid` or set WGA_WID_LOCAL."
        )

    frames = []
    n_files_with_data = 0
    for f in files:
        try:
            df = _read_country_csv(f)
        except Exception as exc:  # noqa: BLE001
            log.warning("Skipping %s: %s", f, exc)
            continue
        df = df[df["variable"].isin(ALL_VARS)]
        if not df.empty:
            frames.append(df)
            n_files_with_data += 1

    if not frames:
        raise RuntimeError("WID files were present but contained no target variables")

    long = pd.concat(frames, ignore_index=True)
    log.info("WID long frame: %d rows across %d countries with data",
             len(long), n_files_with_data)

    g   = _pick_first_available(long, GINI_VARS_ORDERED,   "p0p100")
    m   = _pick_first_available(long, MEAN_VARS_ORDERED,   "p0p100")
    med = _pick_first_available(long, MEDIAN_VARS_ORDERED, "p0p100")

    g   = g.rename(columns={"value": "wealth_gini_raw_source", "var_used": "gini_var"})
    m   = m.rename(columns={"value": "mean_net_wealth",         "var_used": "mean_var"})
    med = med.rename(columns={"value": "median_net_wealth",     "var_used": "median_var"})

    share_dfs = []
    for col_name, bracket in SHARE_BRACKETS.items():
        s = _pick_first_available(long, SHARE_VARS_ORDERED, bracket)
        s = s.rename(columns={"value": f"{col_name}_wealth_share",
                              "var_used": f"{col_name}_var"})
        share_dfs.append(s)

    out = g
    for f in [m, med, *share_dfs]:
        out = out.merge(f, on=["country", "year"], how="outer")

    out = out.dropna(subset=["country", "year"]).reset_index(drop=True)
    out = out.sort_values(["country", "year"]).reset_index(drop=True)
    return out
