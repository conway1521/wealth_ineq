"""Household Finance and Consumption Survey (HFCS) ingest.

The ECB / Eurosystem HFCS publishes harmonized household wealth
distributional indicators across four waves so far for the euro
area plus several non-euro EU members. HFCS is the strongest source
for Tier-A, household-basis wealth inequality in Europe -- the
survey instrument and concept boundaries are explicitly aligned
across countries.

Source files
------------

The ECB publishes per-wave "Statistical Tables" workbooks (XLSX) on
the HFCS Network publications page:
    https://www.ecb.europa.eu/pub/economic-research/research-networks/html/researcher_hfcn.en.html

This module reads those workbooks directly (auto-detecting wave
year from the filename) when they are present under
``data/raw/hfcs/``. It also accepts a pre-converted tidy CSV at
``data/raw/hfcs/hfcs_indicators.csv`` (override via
``WGA_HFCS_LOCAL``) so users who maintain a hand-curated table can
keep doing so.

Sheets we read
--------------

* **J4 Net wealth inequality indicators**  -- Gini coefficient,
  top 5% share, top 10% share. HFCS does **not** publish a top 1%
  share or bottom 50% share in this workbook, so those columns
  remain null in the release.
* **F3 Has negative net wealth**  -- share of households with
  strictly negative net wealth, from the "Total population / ALL"
  row.
* **A1 Main aggregates - medians**  -- median net wealth, from
  the "All / DN3001 Net wealth" row (values in EUR thousands;
  converted to EUR here).
* **A2 Main aggregates - means**  -- mean net wealth, same row.

Country coverage by wave (after parsing):

    wave 1 (2010): 15 countries
    wave 2 (2014): 20 countries
    wave 3 (2017): 22 countries
    wave 4 (2021): 22 countries

The euro-area aggregate column is skipped (it is not a country).
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path

import pandas as pd

log = logging.getLogger(__name__)


# Output CSV schema (the contract from v0.2 scaffold) -----------------------

REQUIRED_COLS = {"country", "wave", "year"}
METRIC_COLS = [
    "gini", "mean_net_wealth", "median_net_wealth",
    "neg_wealth_share", "top10_share", "top5_share", "top1_share",
]
DEFAULT_CSV_PATH = "data/raw/hfcs/hfcs_indicators.csv"
DEFAULT_RAW_DIR = "data/raw/hfcs"


# XLSX parsing constants ----------------------------------------------------

SHEET_J4 = "J4 Net wealth inequality ind"
SHEET_F3 = "F3 Has negative net wealth -"
SHEET_A1 = "A1 Main aggregates - medians"
SHEET_A2 = "A2 Main aggregates - means"

# HFCS labels we extract from each sheet
J4_INDICATORS = {
    "top5_share":  "Top 5% share",
    "top10_share": "Top 10% share",
    "gini":        "Gini coefficient",
}

WAVE_REFERENCE_YEAR = {1: 2010, 2: 2014, 3: 2017, 4: 2021}


def _resolve_csv(explicit: Path | str | None) -> Path:
    if explicit is not None:
        return Path(explicit)
    env = os.environ.get("WGA_HFCS_LOCAL")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[2] / DEFAULT_CSV_PATH


def _resolve_raw_dir() -> Path:
    return Path(__file__).resolve().parents[2] / DEFAULT_RAW_DIR


def fetch(*_args, **_kwargs) -> Path:
    """Return the path the parser will read.

    The HFCS workbooks must be downloaded manually from the ECB; we
    do not (yet) hit the ECB SDW REST API. If neither a CSV nor any
    XLSX files are present, raise a helpful instruction.
    """
    csv = _resolve_csv(None)
    if csv.exists():
        return csv

    raw = _resolve_raw_dir()
    if any(raw.glob("*.xlsx")):
        return raw

    raise FileNotFoundError(
        f"No HFCS source found. Either:\n"
        f"  (a) place the ECB Statistical Tables workbooks "
        f"(HFCS_*Statistical*Tables*Wave_*.xlsx) under {raw}/, or\n"
        f"  (b) place a tidy CSV at {csv} matching the schema in "
        f"wealth_gini_atlas/ingest/hfcs.py.\n"
        f"Workbooks are published at "
        f"https://www.ecb.europa.eu/pub/economic-research/research-networks/html/researcher_hfcn.en.html"
    )


# ----- XLSX workbook parsing -----------------------------------------------

_WAVE_FROM_FILENAME = re.compile(r"Wave[_ ](\d{4})", re.IGNORECASE)


def _detect_wave_year(path: Path) -> int | None:
    """Pull the wave reference year out of the workbook filename.

    The ECB filename pattern is "...Wave_2021..." or "...wave 2010..."
    (case- and separator-insensitive).
    """
    m = _WAVE_FROM_FILENAME.search(path.name)
    if not m:
        return None
    return int(m.group(1))


def _to_float(val) -> float | None:
    """Convert a cell value to float, handling suppressions and SEs.

    Returns None for empty, NA, "n.a.", ".", or parenthesized standard
    errors (which sit on the row directly below each data value in the
    ECB workbooks).
    """
    if pd.isna(val):
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    if not s or s in {".", "-", "..", ":", "n.a.", "n/a", "NA"}:
        return None
    if s.startswith("(") and s.endswith(")"):
        return None   # standard error
    try:
        return float(s.replace(",", "").replace("\xa0", ""))
    except ValueError:
        return None


def _find_country_row(sheet: pd.DataFrame) -> dict[int, str]:
    """Locate the row whose cells are mostly 2-letter ISO country codes.

    Returns {column_index: ISO-2 code}. Skips ``euro_area``.
    """
    for ri in range(min(15, len(sheet))):
        row = sheet.iloc[ri]
        cells = [str(v).strip() if pd.notna(v) else "" for v in row]
        iso2 = [
            (i, c) for i, c in enumerate(cells)
            if len(c) == 2 and c.isalpha() and c.isupper()
        ]
        if len(iso2) >= 5:
            return dict(iso2)
    raise ValueError("Could not locate country-code header row")


def _label_for_row(sheet: pd.DataFrame, ri: int, max_label_col: int = 3) -> str:
    """Return the indicator label from the first non-empty label cell.

    Looks across the first ``max_label_col`` columns and returns the
    rightmost non-empty value (HFCS uses a left "section" column and a
    "label" column to its right).
    """
    parts = []
    for ci in range(max_label_col):
        v = sheet.iloc[ri, ci] if ci < sheet.shape[1] else None
        if pd.notna(v):
            s = str(v).strip()
            if s:
                parts.append(s)
    return parts[-1] if parts else ""


def _extract_j4(sheet: pd.DataFrame) -> dict[str, dict[str, float]]:
    """Pull Gini / top-5% / top-10% by country from sheet J4."""
    countries = _find_country_row(sheet)
    out: dict[str, dict[str, float]] = {c: {} for c in countries.values()}

    for ri in range(len(sheet)):
        label = _label_for_row(sheet, ri)
        for key, want in J4_INDICATORS.items():
            if label == want:
                for col, country in countries.items():
                    v = _to_float(sheet.iloc[ri, col])
                    if v is None:
                        continue
                    if key in ("top5_share", "top10_share"):
                        v = v / 100.0     # percentage -> fraction
                    out[country][key] = v
    return out


def _extract_f3(sheet: pd.DataFrame) -> dict[str, float]:
    """Pull the headline negative-net-wealth share by country from F3.

    The "Total population / ALL" row holds the percentage of households
    with strictly negative net wealth across the whole sample.
    """
    countries = _find_country_row(sheet)
    out: dict[str, float] = {}

    for ri in range(len(sheet)):
        c0 = sheet.iloc[ri, 0] if sheet.shape[1] > 0 else None
        c1 = sheet.iloc[ri, 1] if sheet.shape[1] > 1 else None
        s0 = str(c0).strip() if pd.notna(c0) else ""
        s1 = str(c1).strip() if pd.notna(c1) else ""
        if s0 == "Total population" and s1 == "ALL":
            for col, country in countries.items():
                v = _to_float(sheet.iloc[ri, col])
                if v is not None:
                    out[country] = v / 100.0   # percentage -> fraction
            return out
    return out


def _extract_a_main(sheet: pd.DataFrame) -> dict[str, float]:
    """Pull DN3001 Net wealth from the 'All' breakdown of A1 or A2.

    Values in the workbook are in EUR thousands; we convert to EUR.
    """
    countries = _find_country_row(sheet)
    out: dict[str, float] = {}

    in_all_section = False
    for ri in range(len(sheet)):
        c0 = sheet.iloc[ri, 0] if sheet.shape[1] > 0 else None
        c1 = sheet.iloc[ri, 1] if sheet.shape[1] > 1 else None
        s0 = str(c0).strip() if pd.notna(c0) else ""
        s1 = str(c1).strip() if pd.notna(c1) else ""

        if s0 == "All":
            in_all_section = True
        elif s0 and s0 not in {"", "."} and not s0.startswith("("):
            in_all_section = False    # left the All section

        if in_all_section and s1.startswith("DN3001"):
            for col, country in countries.items():
                v = _to_float(sheet.iloc[ri, col])
                if v is not None:
                    out[country] = v * 1000.0
            return out
    return out


def parse_workbooks(raw_dir: Path | None = None) -> pd.DataFrame:
    """Parse every HFCS Statistical Tables workbook in a directory.

    Returns a tidy long frame matching the same schema produced by the
    pre-converted CSV path. One row per (country, wave).
    """
    raw_dir = Path(raw_dir) if raw_dir else _resolve_raw_dir()
    workbooks = sorted(raw_dir.glob("*.xlsx"))
    if not workbooks:
        raise FileNotFoundError(f"No HFCS workbooks under {raw_dir}")

    rows: list[dict] = []
    for wb in workbooks:
        wave_year = _detect_wave_year(wb)
        if wave_year is None:
            log.warning("Skipping %s: cannot infer wave year from filename", wb.name)
            continue
        wave_num = {2010: 1, 2014: 2, 2017: 3, 2021: 4}.get(wave_year)
        log.info("HFCS workbook %s -> wave %s (%d)", wb.name, wave_num, wave_year)

        per_country: dict[str, dict[str, float]] = {}

        j4 = pd.read_excel(wb, sheet_name=SHEET_J4, header=None)
        for c, vals in _extract_j4(j4).items():
            per_country.setdefault(c, {}).update(vals)

        f3 = pd.read_excel(wb, sheet_name=SHEET_F3, header=None)
        for c, v in _extract_f3(f3).items():
            per_country.setdefault(c, {})["neg_wealth_share"] = v

        a1 = pd.read_excel(wb, sheet_name=SHEET_A1, header=None)
        for c, v in _extract_a_main(a1).items():
            per_country.setdefault(c, {})["median_net_wealth"] = v

        a2 = pd.read_excel(wb, sheet_name=SHEET_A2, header=None)
        for c, v in _extract_a_main(a2).items():
            per_country.setdefault(c, {})["mean_net_wealth"] = v

        for country, vals in per_country.items():
            rows.append({
                "country": country,
                "wave": wave_num,
                "year": wave_year,
                "gini":              vals.get("gini"),
                "mean_net_wealth":   vals.get("mean_net_wealth"),
                "median_net_wealth": vals.get("median_net_wealth"),
                "neg_wealth_share":  vals.get("neg_wealth_share"),
                "top10_share":       vals.get("top10_share"),
                "top5_share":        vals.get("top5_share"),
                "top1_share":        None,  # not published in HFCS workbooks
            })

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df["country"] = df["country"].astype("string")
    df["wave"] = df["wave"].astype("Int8")
    df["year"] = df["year"].astype("Int32")
    for c in METRIC_COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce").astype("Float64")

    # Drop rows with no signal
    present_any = df[METRIC_COLS].notna().any(axis=1)
    df = df[present_any].reset_index(drop=True)

    log.info("HFCS workbooks: %d (country, wave) rows", len(df))
    return df


# ----- CSV parsing (kept for users who maintain a hand-curated table) -------

def _parse_csv(path: Path) -> pd.DataFrame:
    with open(path, "r", encoding="utf-8-sig") as f:
        head = f.readline()
    sep = ";" if head.count(";") > head.count(",") else ","

    df = pd.read_csv(path, sep=sep, dtype={"country": "string"})
    df.columns = [c.strip().lower() for c in df.columns]

    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        raise ValueError(f"HFCS CSV is missing required columns: {sorted(missing)}")

    df["country"] = df["country"].str.upper().str.strip()
    df["wave"] = pd.to_numeric(df["wave"], errors="coerce").astype("Int8")
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int32")
    for c in METRIC_COLS:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("Float64")
        else:
            df[c] = pd.Series([pd.NA] * len(df), dtype="Float64")

    df = df.dropna(subset=["country", "wave", "year"]).reset_index(drop=True)
    present_any = df[METRIC_COLS].notna().any(axis=1)
    df = df[present_any].reset_index(drop=True)
    return df


def parse(path: Path | str | None = None) -> pd.DataFrame:
    """Resolve HFCS source: prefer pre-converted CSV, fall back to workbooks.

    Resolution order:
      1. If ``path`` or ``WGA_HFCS_LOCAL`` is set, treat that as
         authoritative -- read it if it exists, raise if it doesn't.
         Do NOT fall through to the default raw directory (this is
         what tests rely on to scope themselves to fixtures).
      2. Otherwise, read ``data/raw/hfcs/hfcs_indicators.csv`` if it
         exists, else parse any ``*.xlsx`` workbooks in
         ``data/raw/hfcs/``.
    """
    explicit_local = path is not None or "WGA_HFCS_LOCAL" in os.environ
    csv = _resolve_csv(path)

    if explicit_local:
        if csv.exists():
            df = _parse_csv(csv)
            log.info("HFCS CSV (explicit): %d rows across %d countries, waves %s",
                     len(df), df["country"].nunique(),
                     sorted(df["wave"].dropna().unique().tolist()))
            return df
        raise FileNotFoundError(
            f"HFCS source not found at the explicit path: {csv}"
        )

    if csv.exists():
        df = _parse_csv(csv)
        log.info("HFCS CSV: %d rows across %d countries, waves %s",
                 len(df), df["country"].nunique(),
                 sorted(df["wave"].dropna().unique().tolist()))
        return df

    raw = _resolve_raw_dir()
    if any(raw.glob("*.xlsx")):
        df = parse_workbooks(raw)
        log.info("HFCS XLSX: %d rows across %d countries, waves %s",
                 len(df), df["country"].nunique(),
                 sorted(df["wave"].dropna().unique().tolist()))
        return df

    raise FileNotFoundError(
        "No HFCS source found. See `wga fetch hfcs` for instructions."
    )
