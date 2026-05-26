# Contributing to the Wealth Gini Atlas

Thanks for taking an interest. This guide explains what the project
wants from contributions and where the leverage is.

## Project disposition

The Atlas is **conservative on definitions and ambitious on
packaging**. We do not invent new inequality measures. We do not
"correct" published wealth series. We translate already-authoritative
work (WID, OECD, HFCS, SCF, DFA) into one tidy, citable, well-typed
panel with explicit comparability metadata.

In practice this means:

* If your contribution adds a row to the release, it should also
  populate `source_dataset`, `source_priority`, `comparability_tier`,
  and `observed_vs_modeled` -- or document why it can't.
* New computational methods (capitalization, small-area models) are
  welcome but ship as `observed_vs_modeled = "modeled"`,
  `comparability_tier = "C"`, and a clear `method_version` bump.

## Setting up

```bash
git clone https://github.com/conway1521/wealth_ineq
cd wealth_ineq
pip install -e ".[dev]"
pytest
```

The end-to-end test runs offline against the bundled fixtures, so
network access is not required for local development.

## How to add a new source

Most contributions will fall into this category. The pattern is:

1. **Create `wealth_gini_atlas/ingest/<source>.py`** with two
   functions:
   * `fetch(...)` downloads raw upstream files into
     `data/raw/<source>/` (or honors `WGA_<SOURCE>_LOCAL` for offline
     mirrors).
   * `parse(...)` returns a tidy pandas DataFrame keyed by
     `(country, year)` (or `(geo_id, year)`).

2. **Create `wealth_gini_atlas/harmonize/<source>.py`** (or extend
   `harmonize/national.py`) with a function that maps the parsed
   frame onto the release schema. Make sure to:
   * Set `geo_id` to ISO-3 (use `harmonize.iso.to_iso3`).
   * Set `unit_of_analysis` to whatever the source publishes natively.
   * Pick a `comparability_tier` (A/B/C) and document the choice in
     the docstring.
   * Pick a `top_tail_flag` (survey_only / admin_enhanced / mixed).

3. **Wire it into the pipeline.** Either add it to
   `wealth_gini_atlas/compute/pipeline.py` or add a new pipeline
   function and a CLI subcommand.

4. **Add a small synthetic fixture** under `data/fixtures/` and a
   test that exercises the new ingest end-to-end without network.

5. **Update `docs/source_priority.md`** with where the new source
   fits in the hierarchy, and bump `CHANGELOG.md`.

## How to add a new country to the v0.1 backbone

You don't have to do anything. `wga fetch wid` pulls every country
WID publishes; the harmonizer accepts any ISO-2 code present in
`wealth_gini_atlas/harmonize/iso.py`. If a country is missing from
the ISO table, add an entry to `ISO2_TO_ISO3` and submit a PR.

## How to add a new variable

If you want a column that isn't in the release schema:

1. Add a `(name, dtype, required)` tuple to `COLUMNS` in
   `wealth_gini_atlas/schema.py`.
2. Add the column to `docs/codebook.yaml` with description, type,
   and (if applicable) a controlled vocabulary.
3. Decide if any validator check applies (range, consistency with
   other columns); add it to `validate()`.
4. Populate the column in the harmonizer for any source that has it,
   and leave it `pd.NA` for sources that don't.
5. Tests, changelog.

## What the release file MUST satisfy

Run `wga validate <path>` before opening a PR. The validator enforces:

* Required columns present and non-null.
* Vocabularies for enum columns (`geo_level`, `wealth_concept`, etc.).
* `wealth_gini` in [0, 1] (the headline series; not `wealth_gini_raw`).
* Shares in [0, 1] with internal consistency:
  * `top1 <= top10`
  * `top10 >= 0.1`, `top1 >= 0.01`
  * `bottom50 <= 0.5`
  * `top10 + bottom50 <= 1` (middle 40% non-negative)
* `mean_net_wealth >= median_net_wealth` (wealth is right-skewed).
* No duplicates on the natural key
  `(geo_id, year, wealth_concept, unit_of_analysis, source_dataset)`.

If your contribution legitimately violates one of these (e.g. an
admin-enhanced top share with a different definition of "top 1%"),
flag it in `notes` and in the PR description.

## Style

* `ruff check wealth_gini_atlas tests` should be clean.
* Public functions get one-line docstrings unless the docstring is
  carrying a methodological note.
* Tests live in `tests/` and mirror the package layout.
* Imports: standard library, then third-party, then local; sorted
  within each block.

## Commit messages

Imperative mood, short subject, longer body if the change is
non-trivial. Reference the relevant section of `docs/methods.md` or
the project brief when you make a methodological choice.

## Reporting issues

Use GitHub Issues. For data-quality issues, please include:

* The `geo_id`, `year`, `source_dataset` of the affected row(s).
* The expected vs observed value.
* A link to a primary-source publication that supports the
  expected value.
