"""End-to-end pipeline: WID (+ HFCS when available) -> harmonized release frame.

The release table is a stacked union of rows from each source. Multiple
sources may contribute a row for the same (geo_id, year, wealth_concept,
unit_of_analysis) cell -- they are distinguished by ``source_dataset``,
and downstream users filter by ``comparability_tier`` or
``source_priority`` to choose which series to lean on.
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


def _build_wid(raw_dir: Path | None) -> pd.DataFrame:
    log.info("Parsing WID files")
    try:
        wid_wide = wid_ingest.parse(raw_dir=raw_dir)
    except FileNotFoundError as exc:
        log.warning("WID source not available, skipping: %s", exc)
        return empty_frame()
    log.info("Read %d WID country-year observations", len(wid_wide))
    df = harm.from_wid(wid_wide)
    log.info("WID release rows: %d", len(df))
    return df


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


def build_release(raw_dir: Path | None = None) -> pd.DataFrame:
    """Run the v0.1+ pipeline and return a validated release DataFrame."""
    parts = [_build_wid(raw_dir), _build_hfcs()]
    parts = [p for p in parts if not p.empty]
    if not parts:
        log.warning("No source produced any rows; release frame is empty")
        return empty_frame()

    df = pd.concat(parts, ignore_index=True)
    df = df.drop_duplicates(subset=["geo_id", "year", "wealth_concept",
                                    "unit_of_analysis", "source_dataset"])
    log.info(
        "Combined release: %d rows, %d countries, %d sources, years %s..%s",
        len(df),
        df["geo_id"].nunique(),
        df["source_dataset"].nunique(),
        int(df["year"].min()),
        int(df["year"].max()),
    )

    issues = validate(df, strict=False)
    if issues:
        log.warning("Schema validation surfaced %d issues:", len(issues))
        for i in issues:
            log.warning("  - %s", i)
    return df
