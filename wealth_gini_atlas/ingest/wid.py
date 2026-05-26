"""World Inequality Database (WID) ingest for the v0.1 backbone.

WID publishes per-country bulk CSVs at
    https://wid.world/bulk_download/

Each file is named ``WID_data_<ISO2>.csv`` (semicolon-delimited) plus a
companion ``WID_metadata_<ISO2>.csv`` describing units and methods.
Rows are long-format with the following columns of interest:

    country     ISO-2 code (e.g. "FR", "US", "DE")
    variable    code (e.g. "ghweal992j", "shweal992j", "ahweal992j")
    percentile  percentile bracket (e.g. "p0p100", "p90p100", "p99p100",
                "p0p50") -- shares are stored as a row per bracket
    year        integer
    value       float; shares are on a 0..1 scale, Gini on 0..1, money
                in local currency or, in the "metadata" file's unit, EUR

Variable codes used in v0.1
---------------------------

* ``ghweal992j``  Gini coefficient of net personal wealth, equal-split adults
* ``shweal992j``  share of net personal wealth, equal-split adults
                  (the percentile column selects p90p100, p99p100, p0p50)
* ``ahweal992j``  average net personal wealth per equal-split adult
* ``mhweal992j``  median net personal wealth per equal-split adult (when
                  published)

We use the equal-split-adults (``992j``) population because that is
WID's headline cross-country wealth basis and what their published Gini
series is calibrated for. The release file therefore marks
``unit_of_analysis = per_adult_equal_split`` for all WID-sourced rows.

Network
-------

Some sandboxed environments do not allow outbound HTTPS to wid.world.
``fetch()`` therefore reads from a local mirror directory if one is set
via the ``WGA_WID_LOCAL`` environment variable. The expected layout is::

    $WGA_WID_LOCAL/WID_data_FR.csv
    $WGA_WID_LOCAL/WID_data_US.csv
    ...

You can either point that at an unzipped WID bulk download or run
``make data-wid`` on a machine with network access.
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
WID_PER_COUNTRY_URL_TMPL = "https://wid.world/bulk_download/WID_data_{iso2}.csv"

VARIABLES = {
    "gini":   "ghweal992j",
    "share":  "shweal992j",   # combined with percentile column
    "mean":   "ahweal992j",
    "median": "mhweal992j",
}

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
          timeout: int = 60) -> Path:
    """Download WID bulk data into ``data/raw/wid/``.

    If the ``WGA_WID_LOCAL`` environment variable is set, this is a
    no-op: the local directory is treated as the source of truth and
    its path is returned.
    """
    local = os.environ.get("WGA_WID_LOCAL")
    if local:
        p = Path(local)
        if not p.is_dir():
            raise FileNotFoundError(f"WGA_WID_LOCAL={local} is not a directory")
        log.info("Using local WID mirror at %s", p)
        return p

    out = _raw_dir(root)
    if countries:
        # Per-country pull -- lighter and easier to debug than the full zip.
        for iso2 in countries:
            url = WID_PER_COUNTRY_URL_TMPL.format(iso2=iso2.upper())
            dest = out / f"WID_data_{iso2.upper()}.csv"
            log.info("Fetching %s -> %s", url, dest)
            r = requests.get(url, timeout=timeout)
            r.raise_for_status()
            dest.write_bytes(r.content)
        return out

    # Bulk pull
    log.info("Fetching WID bulk archive %s", WID_BULK_URL)
    r = requests.get(WID_BULK_URL, timeout=timeout, stream=True)
    r.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
        zf.extractall(out)
    return out


def _read_country_csv(path: Path) -> pd.DataFrame:
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


def parse(raw_dir: Path | None = None) -> pd.DataFrame:
    """Return a tidy wide frame keyed by (country, year) with our v0.1 variables.

    Columns: country (ISO-2), year, wealth_gini, top10_wealth_share,
    top1_wealth_share, bottom50_wealth_share, mean_net_wealth,
    median_net_wealth.
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
    keep_vars = set(VARIABLES.values())
    for f in files:
        try:
            df = _read_country_csv(f)
        except Exception as exc:  # noqa: BLE001
            log.warning("Skipping %s: %s", f, exc)
            continue
        df = df[df["variable"].isin(keep_vars)]
        frames.append(df)

    if not frames:
        raise RuntimeError("WID files were present but contained no target variables")

    long = pd.concat(frames, ignore_index=True)

    # ---- Gini and mean / median: one value per (country, year) -----------
    def _pivot_scalar(varcode: str, out_col: str) -> pd.DataFrame:
        s = long[(long["variable"] == varcode) & (long["percentile"].isin(["p0p100", ""])
                                                  | long["percentile"].isna())]
        # For Gini and means, WID uses percentile = "p0p100" (whole pop)
        s = long[(long["variable"] == varcode) & (long["percentile"] == "p0p100")]
        out = s[["country", "year", "value"]].rename(columns={"value": out_col})
        return out

    gini_df = _pivot_scalar(VARIABLES["gini"], "wealth_gini_raw_source")
    mean_df = _pivot_scalar(VARIABLES["mean"], "mean_net_wealth")
    median_df = _pivot_scalar(VARIABLES["median"], "median_net_wealth")

    # ---- Shares: one row per percentile bracket --------------------------
    sh = long[long["variable"] == VARIABLES["share"]]
    share_frames = []
    for out_col, bracket in SHARE_BRACKETS.items():
        sub = sh[sh["percentile"] == bracket]
        share_frames.append(
            sub[["country", "year", "value"]].rename(columns={"value": f"{out_col}_wealth_share"})
        )

    out = gini_df
    for f in [mean_df, median_df, *share_frames]:
        out = out.merge(f, on=["country", "year"], how="outer")

    # Tidy
    out = out.dropna(subset=["country", "year"]).reset_index(drop=True)
    out = out.sort_values(["country", "year"]).reset_index(drop=True)
    return out
