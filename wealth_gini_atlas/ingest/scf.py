"""Survey of Consumer Finances (SCF) ingest -- v0.3 scaffold.

The SCF is the Federal Reserve Board's triennial household-wealth
survey for the United States. It is the strongest US source for
household-basis net wealth, mean / median, and percentile shares.
The SCF chartbook does **not** publish a Gini coefficient -- the
Gini requires the public-use microdata (five implicates plus
replicate weights, Rubin's-rules averaging) which is out of scope
for v0.3. SCF rows therefore enter the Moments Atlas, not the
Gini Atlas.

Source files we expect
----------------------

Two paths to obtain SCF distributional summary statistics. Pick the
one that matches what the user has downloaded.

* **SCF chartbook XLSX** (the published chartbook supplement):
  https://www.federalreserve.gov/econres/scfindex.htm
  Place under ``data/raw/scf/`` (any filename matching ``scf*.xlsx``).
  The chartbook contains aggregated mean / median / percentile-share
  tables across the survey years (1989, 1992, ..., 2022).
* **SCF Bulletin Article supplementary tables** (per survey year):
  https://www.federalreserve.gov/publications/files/scf22.pdf and
  the accompanying ``scf2022_tables_for_internet.xlsx``-style
  workbooks. Also goes under ``data/raw/scf/``.

Survey years and reference dates (2022 release):

    1989, 1992, 1995, 1998, 2001, 2004, 2007, 2010, 2013, 2016, 2019, 2022

Harmonization contract
----------------------

* ``unit_of_analysis = "household"`` (SCF "primary economic unit").
* ``equivalence_scale = "none"``.
* ``currency = "USD"`` (2022 dollars for the most recent release;
  the chartbook nominalizes earlier waves to a common base).
* ``source_dataset = "SCF"``.
* ``source_priority = "tier1"``.
* ``comparability_tier = "B"`` (against HFCS at the country level --
  different sampling, different concept boundaries).
* ``top_tail_flag = "survey_only"`` for SCF chartbook rows;
  Saez-Zucman-style admin-enhanced US series enter as a separate
  source.
* ``observed_vs_modeled = "imported"``.

Implementation status
---------------------

This module is a scaffold. ``harmonize_frame()`` raises
``FileNotFoundError`` if no SCF source files exist under
``data/raw/scf/``, which the pipeline catches and treats as
"SCF rows not yet available". When you commit a chartbook XLSX,
this module's parser will be filled in against the real file
structure (same iteration pattern as HFCS).
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import pandas as pd

from .. import METHOD_VERSION
from ..schema import conform, empty_frame

log = logging.getLogger(__name__)


DEFAULT_RAW_DIR = "data/raw/scf"


def _resolve_raw_dir() -> Path:
    env = os.environ.get("WGA_SCF_LOCAL")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[2] / DEFAULT_RAW_DIR


def fetch(*_args, **_kwargs) -> Path:
    raw = _resolve_raw_dir()
    if any(raw.glob("scf*.xlsx")) or any(raw.glob("scf*.csv")):
        return raw
    raise FileNotFoundError(
        f"No SCF source files found under {raw}.\n"
        "Expected: SCF chartbook XLSX or Bulletin Article supplementary "
        "tables from https://www.federalreserve.gov/econres/scfindex.htm "
        "(filename matching scf*.xlsx or scf*.csv).\n"
        "See wealth_gini_atlas/ingest/scf.py docstring for details."
    )


def parse(raw_dir: Path | None = None) -> pd.DataFrame:
    """Parse SCF source files into a tidy frame keyed by (year,).

    Returns columns: year, mean_net_wealth, median_net_wealth,
    top10_share, top5_share, top1_share, bottom50_share,
    neg_wealth_share. All optional except year.
    """
    raise NotImplementedError(
        "SCF parse() not yet implemented. Commit an SCF chartbook XLSX "
        "to data/raw/scf/ and the parser will be wired in against the "
        "real file structure -- same iteration loop as HFCS."
    )


def harmonize_frame(raw_dir: Path | None = None) -> pd.DataFrame:
    """Return SCF rows ready for the Moments Atlas (release schema)."""
    fetch()              # raise FileNotFoundError if nothing on disk
    df_long = parse(raw_dir)
    if df_long.empty:
        return empty_frame()

    rows = []
    for _, r in df_long.iterrows():
        rows.append({
            "geo_id": "USA",
            "geo_name": "United States",
            "geo_level": "country",
            "year": int(r["year"]) if pd.notna(r.get("year")) else pd.NA,
            "wealth_concept": "net_wealth",
            "wealth_gini": pd.NA,
            "wealth_gini_raw": pd.NA,
            "negative_wealth_share": r.get("neg_wealth_share"),
            "mean_net_wealth":   r.get("mean_net_wealth"),
            "median_net_wealth": r.get("median_net_wealth"),
            "top10_wealth_share": r.get("top10_share"),
            "top1_wealth_share":  r.get("top1_share"),
            "bottom50_wealth_share": r.get("bottom50_share"),
            "unit_of_analysis": "household",
            "equivalence_scale": "none",
            "currency": "USD",
            "source_dataset": "SCF",
            "source_priority": "tier1",
            "comparability_tier": "B",
            "observed_vs_modeled": "imported",
            "top_tail_flag": "survey_only",
            "method_version": METHOD_VERSION,
            "notes": "Imported from SCF chartbook (moments-only, no Gini).",
        })
    df = pd.DataFrame(rows).dropna(subset=["year"])
    return conform(df)
