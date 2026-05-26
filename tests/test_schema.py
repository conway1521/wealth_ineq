"""Schema conformance and validator behavior."""

from __future__ import annotations

import pandas as pd
import pytest

from wealth_gini_atlas.schema import (
    COLUMN_ORDER,
    SchemaError,
    conform,
    empty_frame,
    validate,
)


def _row(**overrides):
    base = {
        "geo_id": "FRA", "geo_name": "France", "geo_level": "country",
        "year": 2020, "wealth_concept": "net_wealth", "wealth_gini": 0.7,
        "unit_of_analysis": "per_adult_equal_split", "equivalence_scale": "none",
        "source_dataset": "WID", "source_priority": "tier1",
        "comparability_tier": "B", "observed_vs_modeled": "imported",
        "method_version": "wga-0.1",
    }
    base.update(overrides)
    return base


def test_empty_frame_has_full_schema():
    df = empty_frame()
    assert list(df.columns) == COLUMN_ORDER


def test_conform_fills_missing_optional_columns():
    df = pd.DataFrame([_row()])
    out = conform(df)
    assert list(out.columns) == COLUMN_ORDER
    assert out["negative_wealth_share"].isna().all()


def test_validate_passes_on_clean_frame():
    df = conform(pd.DataFrame([_row(), _row(year=2021)]))
    assert validate(df, strict=False) == []


def test_validate_flags_out_of_range_gini():
    df = conform(pd.DataFrame([_row(wealth_gini=1.5)]))
    issues = validate(df, strict=False)
    assert any("wealth_gini" in i for i in issues)


def test_validate_flags_bad_vocab():
    df = conform(pd.DataFrame([_row(geo_level="planet")]))
    issues = validate(df, strict=False)
    assert any("geo_level" in i for i in issues)


def test_validate_flags_duplicate_key():
    df = conform(pd.DataFrame([_row(), _row()]))  # exact duplicate
    issues = validate(df, strict=False)
    assert any("duplicate" in i for i in issues)


def test_strict_mode_raises():
    df = conform(pd.DataFrame([_row(wealth_gini=99.0)]))
    with pytest.raises(SchemaError):
        validate(df, strict=True)


# --- Internal consistency checks --------------------------------------------

def test_validate_flags_top1_above_top10():
    df = conform(pd.DataFrame([_row(top1_wealth_share=0.30,
                                    top10_wealth_share=0.20)]))
    issues = validate(df, strict=False)
    assert any("top1_wealth_share > top10_wealth_share" in i for i in issues)


def test_validate_flags_top10_below_floor():
    df = conform(pd.DataFrame([_row(top10_wealth_share=0.05)]))
    issues = validate(df, strict=False)
    assert any("top10_wealth_share < 0.10" in i for i in issues)


def test_validate_flags_top1_below_floor():
    df = conform(pd.DataFrame([_row(top1_wealth_share=0.005,
                                    top10_wealth_share=0.30)]))
    issues = validate(df, strict=False)
    assert any("top1_wealth_share < 0.01" in i for i in issues)


def test_validate_flags_bottom50_above_half():
    df = conform(pd.DataFrame([_row(bottom50_wealth_share=0.65)]))
    issues = validate(df, strict=False)
    assert any("bottom50_wealth_share > 0.5" in i for i in issues)


def test_validate_flags_top_plus_bottom_exceeding_one():
    df = conform(pd.DataFrame([_row(top10_wealth_share=0.80,
                                    bottom50_wealth_share=0.40,
                                    top1_wealth_share=0.40)]))
    issues = validate(df, strict=False)
    assert any("middle 40% negative" in i for i in issues)


def test_validate_flags_mean_below_median():
    df = conform(pd.DataFrame([_row(mean_net_wealth=50_000,
                                    median_net_wealth=80_000)]))
    issues = validate(df, strict=False)
    assert any("right-skewed wealth distributions" in i for i in issues)


def test_validate_accepts_partial_shares():
    # bottom50 missing -> the top10+bottom50 check should NOT fire.
    df = conform(pd.DataFrame([_row(top10_wealth_share=0.7,
                                    top1_wealth_share=0.3)]))
    issues = validate(df, strict=False)
    assert not any("top10 + bottom50" in i for i in issues)
