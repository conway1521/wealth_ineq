"""US long-run wealth distribution composite series.

Stitches the two US Moments Atlas sources into a single analysis-ready
annual frame covering 1989–present:

  DFA (annual, Q4 snapshots)   -- top-1%, top-10%, bottom-50% shares
  SCF (triennial, 1989-2022)   -- mean, median, top-10%, bottom-50%

Design choices
--------------
* **Shares**: DFA is preferred over SCF for all percentile-share
  columns because it is annual (higher frequency), anchored to
  Financial Accounts aggregates (admin-enhanced top tail), and
  published at quarterly frequency so the Q4 snapshot is a
  clean year-end observation.
* **Mean / median**: SCF is the only source for these. They are
  carried as-is (triennial, in 2022 USD) and linearly interpolated
  to annual frequency in the interpolated series. Raw triennial values
  are preserved in ``mean_net_wealth_scf`` / ``median_net_wealth_scf``.
* **top-10 cross-check**: both sources supply top-10, so we keep both
  columns (``top10_dfa`` and ``top10_scf``) for diagnostic use.
  A ``top10_gap`` column shows DFA - SCF; persistent sign flips signal
  methodology drift worth investigating.

Output columns (``build_composite``)
-------------------------------------

  year                  int, 1989-2025
  top1_share            float, DFA (admin-enhanced)
  top10_share           float, DFA (admin-enhanced)
  top10_share_scf       float, SCF chartbook (survey, triennial, NaN in gap years)
  bottom50_share        float, DFA
  bottom50_share_scf    float, SCF (triennial, NaN in gap years)
  top10_gap             float, DFA top10 - SCF top10 (NaN where SCF absent)
  mean_net_wealth_scf   float, SCF 2022 USD (triennial, NaN in gap years)
  median_net_wealth_scf float, SCF 2022 USD (triennial, NaN in gap years)
  mean_net_wealth_interp   float, SCF linearly interpolated to annual
  median_net_wealth_interp float, SCF linearly interpolated to annual
  source_shares         str, always "DFA"
  source_moments        str, "SCF" where available, "SCF_interp" otherwise

Usage
-----
    from wealth_gini_atlas.analysis.us_longrun import build_composite

    df = build_composite()           # loads from the default release dir
    df = build_composite("data/release/wealth_moments_atlas_v0.3.0.parquet")
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

log = logging.getLogger(__name__)

_DEFAULT_RELEASE_GLOB = "data/release/wealth_moments_atlas_v*.parquet"


def _latest_moments_atlas() -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    candidates = sorted((repo_root / "data" / "release").glob(
        "wealth_moments_atlas_v*.parquet"))
    if not candidates:
        raise FileNotFoundError(
            "No wealth_moments_atlas_v*.parquet found under data/release/. "
            "Run `wga build --out-dir data/release` first."
        )
    return candidates[-1]          # highest version (lexicographic)


def build_composite(
    moments_path: str | Path | None = None,
) -> pd.DataFrame:
    """Return the US long-run composite series as a tidy annual DataFrame.

    Parameters
    ----------
    moments_path
        Path to a ``wealth_moments_atlas_v*.parquet`` (or ``.csv``) file.
        If None, uses the highest-version file under ``data/release/``.
    """
    if moments_path is None:
        moments_path = _latest_moments_atlas()

    path = Path(moments_path)
    atlas = (pd.read_parquet(path) if path.suffix == ".parquet"
             else pd.read_csv(path))

    usa = atlas[atlas["geo_id"] == "USA"].copy()
    if usa.empty:
        raise ValueError("No USA rows found in the Moments Atlas.")

    dfa = (usa[usa["source_dataset"] == "DFA"]
           .sort_values("year")
           [["year", "top1_wealth_share", "top10_wealth_share",
             "bottom50_wealth_share"]]
           .rename(columns={
               "top1_wealth_share":    "top1_share",
               "top10_wealth_share":   "top10_share",
               "bottom50_wealth_share": "bottom50_share",
           })
           .set_index("year"))

    scf = (usa[usa["source_dataset"] == "SCF"]
           .sort_values("year")
           [["year", "mean_net_wealth", "median_net_wealth",
             "top10_wealth_share", "bottom50_wealth_share"]]
           .rename(columns={
               "top10_wealth_share":    "top10_share_scf",
               "bottom50_wealth_share": "bottom50_share_scf",
               "mean_net_wealth":       "mean_net_wealth_scf",
               "median_net_wealth":     "median_net_wealth_scf",
           })
           .set_index("year"))

    if dfa.empty:
        raise ValueError("No DFA rows found in the Moments Atlas.")
    if scf.empty:
        log.warning("No SCF rows found; mean/median columns will be empty.")

    # Outer join on year index so DFA fills all annual slots
    comp = dfa.join(scf, how="left")
    comp.index.name = "year"
    comp = comp.reset_index()

    # Top-10 gap: DFA annual minus SCF triennial (NaN in SCF gap years)
    comp["top10_gap"] = comp["top10_share"] - comp["top10_share_scf"]

    # Linearly interpolate mean/median to annual (SCF triennial anchor points).
    # Only interpolate BETWEEN anchor points; years beyond the last SCF survey
    # stay NaN rather than flat-carrying the final value.
    last_scf_year = int(comp.loc[comp["mean_net_wealth_scf"].notna(), "year"].max())
    for col in ("mean_net_wealth_scf", "median_net_wealth_scf"):
        interp_col = col.replace("_scf", "_interp")
        s = comp.set_index("year")[col]
        s_interp = (s.reindex(range(comp["year"].min(), comp["year"].max() + 1))
                     .interpolate(method="index"))
        # Zero out anything beyond the last SCF anchor so we don't imply data exists
        s_interp.loc[s_interp.index > last_scf_year] = float("nan")
        comp[interp_col] = s_interp.values

    # Source attribution flags
    comp["source_shares"]  = "DFA"
    comp["source_moments"] = comp["mean_net_wealth_scf"].apply(
        lambda v: "SCF" if pd.notna(v) else "SCF_interp"
    )

    # Reorder columns for readability
    ordered = [
        "year",
        "top1_share", "top10_share", "top10_share_scf", "top10_gap",
        "bottom50_share", "bottom50_share_scf",
        "mean_net_wealth_scf", "median_net_wealth_scf",
        "mean_net_wealth_interp", "median_net_wealth_interp",
        "source_shares", "source_moments",
    ]
    comp = comp[[c for c in ordered if c in comp.columns]]

    log.info(
        "US long-run series: %d annual obs, %d–%d, "
        "%d SCF triennial anchor points",
        len(comp), int(comp["year"].min()), int(comp["year"].max()),
        int(comp["mean_net_wealth_scf"].notna().sum()),
    )
    return comp
