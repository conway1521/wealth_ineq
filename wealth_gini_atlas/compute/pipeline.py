"""End-to-end v0.1 pipeline: WID -> harmonized release frame."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from ..ingest import wid as wid_ingest
from ..harmonize import national as harm
from ..schema import validate

log = logging.getLogger(__name__)


def build_release(raw_dir: Path | None = None) -> pd.DataFrame:
    """Run the v0.1 pipeline and return a validated release DataFrame."""
    log.info("Parsing WID files")
    wid_wide = wid_ingest.parse(raw_dir=raw_dir)
    log.info("Read %d WID country-year observations", len(wid_wide))

    log.info("Harmonizing to release schema")
    df = harm.from_wid(wid_wide)
    log.info("Release frame: %d rows, %d countries, years %s..%s",
             len(df),
             df["geo_id"].nunique() if not df.empty else 0,
             int(df["year"].min()) if not df.empty else "n/a",
             int(df["year"].max()) if not df.empty else "n/a")

    issues = validate(df, strict=False)
    if issues:
        log.warning("Schema validation surfaced %d issues:", len(issues))
        for i in issues:
            log.warning("  - %s", i)
    return df
