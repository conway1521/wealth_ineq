"""Release-table schema for the Wealth Gini Atlas.

The schema is intentionally flat and long-format: one row per
(geo_id, year, wealth_concept, unit_of_analysis, source_dataset).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pandas as pd

# --- Controlled vocabularies ------------------------------------------------

GEO_LEVELS = {"country", "nuts2", "us_state", "region_other"}

WEALTH_CONCEPTS = {
    "net_wealth",          # headline: assets - liabilities
    "net_financial_wealth",
    "net_housing_wealth",
    "non_financial_wealth",
}

UNITS_OF_ANALYSIS = {
    "household",
    "per_adult_equal_split",   # WID convention
    "per_adult",
    "individual",
}

EQUIVALENCE_SCALES = {
    "none",
    "oecd_modified",
    "sqrt",
}

COMPARABILITY_TIERS = {"A", "B", "C"}

OBSERVED_VS_MODELED = {"observed", "imported", "modeled", "mixed"}

SOURCE_PRIORITY = {"tier1", "tier2"}

# --- Column definitions -----------------------------------------------------

# (column_name, pandas_dtype, required)
COLUMNS: list[tuple[str, str, bool]] = [
    ("geo_id",                "string",  True),
    ("geo_name",              "string",  True),
    ("geo_level",             "string",  True),
    ("year",                  "Int32",   True),
    ("wealth_concept",        "string",  True),
    ("wealth_gini",           "Float64", True),    # headline Gini with negatives->0
    ("wealth_gini_raw",       "Float64", False),   # optional: Gini before negative-zeroing
    ("negative_wealth_share", "Float64", False),
    ("mean_net_wealth",       "Float64", False),
    ("median_net_wealth",     "Float64", False),
    ("top10_wealth_share",    "Float64", False),
    ("top1_wealth_share",     "Float64", False),
    ("bottom50_wealth_share", "Float64", False),
    ("unit_of_analysis",      "string",  True),
    ("equivalence_scale",     "string",  True),
    ("currency",              "string",  False),
    ("source_dataset",        "string",  True),
    ("source_priority",       "string",  True),
    ("comparability_tier",    "string",  True),
    ("observed_vs_modeled",   "string",  True),
    ("top_tail_flag",         "string",  False),    # e.g. "survey_only", "admin_enhanced"
    ("method_version",        "string",  True),
    ("notes",                 "string",  False),
]

COLUMN_ORDER = [c for c, _, _ in COLUMNS]
DTYPES = {c: d for c, d, _ in COLUMNS}
REQUIRED = [c for c, _, r in COLUMNS if r]


@dataclass(frozen=True)
class SchemaError(Exception):
    """Raised when a release frame violates the schema."""
    message: str

    def __str__(self) -> str:
        return self.message


def empty_frame() -> pd.DataFrame:
    """Return an empty DataFrame with the release schema applied."""
    df = pd.DataFrame({c: pd.Series(dtype=d) for c, d, _ in COLUMNS})
    return df[COLUMN_ORDER]


def conform(df: pd.DataFrame) -> pd.DataFrame:
    """Reorder columns, coerce dtypes, and fill missing optional columns."""
    out = df.copy()
    for c, d, _ in COLUMNS:
        if c not in out.columns:
            out[c] = pd.Series([pd.NA] * len(out), dtype=d)
        else:
            try:
                out[c] = out[c].astype(d)
            except (TypeError, ValueError) as exc:
                raise SchemaError(f"Column {c!r} cannot be cast to {d}: {exc}") from exc
    return out[COLUMN_ORDER]


def validate(df: pd.DataFrame, *, strict: bool = True) -> list[str]:
    """Check the release frame; return a list of human-readable issues.

    With strict=True, raises SchemaError if any issue is found.
    """
    issues: list[str] = []

    missing_required = [c for c in REQUIRED if c not in df.columns]
    if missing_required:
        issues.append(f"missing required columns: {missing_required}")
        if strict:
            raise SchemaError("; ".join(issues))
        return issues

    # Required-column null checks
    for c in REQUIRED:
        n_null = df[c].isna().sum()
        if n_null:
            issues.append(f"required column {c!r} has {n_null} nulls")

    # Vocabulary checks
    def _check_vocab(col: str, vocab: Iterable[str]) -> None:
        bad = set(df[col].dropna().unique()) - set(vocab)
        if bad:
            issues.append(f"{col} has out-of-vocab values: {sorted(bad)}")

    _check_vocab("geo_level", GEO_LEVELS)
    _check_vocab("wealth_concept", WEALTH_CONCEPTS)
    _check_vocab("unit_of_analysis", UNITS_OF_ANALYSIS)
    _check_vocab("equivalence_scale", EQUIVALENCE_SCALES)
    _check_vocab("comparability_tier", COMPARABILITY_TIERS)
    _check_vocab("observed_vs_modeled", OBSERVED_VS_MODELED)
    _check_vocab("source_priority", SOURCE_PRIORITY)

    # Numeric range checks for Gini and shares (post-negative-zeroing)
    if "wealth_gini" in df.columns:
        g = df["wealth_gini"].dropna()
        if ((g < 0) | (g > 1)).any():
            issues.append("wealth_gini values fall outside [0, 1]")

    share_cols = [c for c in ("top10_wealth_share", "top1_wealth_share",
                              "bottom50_wealth_share", "negative_wealth_share")
                  if c in df.columns]
    for c in share_cols:
        s = df[c].dropna()
        # WID stores shares on a 0-1 scale; we'll normalize before write.
        if ((s < -0.5) | (s > 1.5)).any():
            issues.append(f"{c} values look outside plausible 0..1 range")

    # Uniqueness of the natural key
    key = ["geo_id", "year", "wealth_concept", "unit_of_analysis", "source_dataset"]
    if set(key).issubset(df.columns):
        dups = df.duplicated(subset=key).sum()
        if dups:
            issues.append(f"{dups} duplicate rows on natural key {key}")

    # Internal consistency of distributional shares
    # ---------------------------------------------
    # Wealth distributions are right-skewed, so the following bounds must
    # hold by construction (allowing a small tolerance for rounding in the
    # upstream publication):
    #   * top1 <= top10                         (nested percentile groups)
    #   * 0.10 <= top10 <= 1.0                  (top decile holds >=10%)
    #   * 0.01 <= top1  <= 1.0                  (top centile holds >=1%)
    #   * 0    <= bottom50 <= 0.5               (bottom half holds <=50%)
    #   * top10 + bottom50 <= 1.0               (middle 40% share non-neg)
    #   * mean_net_wealth >= median_net_wealth  (right-skew of wealth)
    tol = 1e-6

    def _bad(col: str, mask: "pd.Series") -> int:
        return int(mask.fillna(False).sum())

    if {"top1_wealth_share", "top10_wealth_share"}.issubset(df.columns):
        n = _bad("top1>top10",
                 df["top1_wealth_share"] > df["top10_wealth_share"] + tol)
        if n:
            issues.append(f"{n} rows have top1_wealth_share > top10_wealth_share")

    if "top10_wealth_share" in df.columns:
        s = df["top10_wealth_share"]
        n = _bad("top10<0.10", (s < 0.10 - tol) & s.notna())
        if n:
            issues.append(f"{n} rows have top10_wealth_share < 0.10 (impossible)")

    if "top1_wealth_share" in df.columns:
        s = df["top1_wealth_share"]
        n = _bad("top1<0.01", (s < 0.01 - tol) & s.notna())
        if n:
            issues.append(f"{n} rows have top1_wealth_share < 0.01 (impossible)")

    if "bottom50_wealth_share" in df.columns:
        s = df["bottom50_wealth_share"]
        n = _bad("bottom50>0.5", s > 0.5 + tol)
        if n:
            issues.append(f"{n} rows have bottom50_wealth_share > 0.5 (impossible)")

    if {"top10_wealth_share", "bottom50_wealth_share"}.issubset(df.columns):
        s = df["top10_wealth_share"].fillna(0) + df["bottom50_wealth_share"].fillna(0)
        # Only flag when both shares are present; otherwise the sum is partial.
        both = df["top10_wealth_share"].notna() & df["bottom50_wealth_share"].notna()
        n = _bad("top10+bottom50>1", (s > 1.0 + tol) & both)
        if n:
            issues.append(f"{n} rows have top10 + bottom50 > 1 (middle 40% negative)")

    if {"mean_net_wealth", "median_net_wealth"}.issubset(df.columns):
        both = df["mean_net_wealth"].notna() & df["median_net_wealth"].notna()
        n = _bad("mean<median",
                 (df["mean_net_wealth"] < df["median_net_wealth"] - tol) & both)
        if n:
            issues.append(
                f"{n} rows have mean_net_wealth < median_net_wealth "
                "(unexpected for right-skewed wealth distributions)"
            )

    if strict and issues:
        raise SchemaError("; ".join(issues))
    return issues
