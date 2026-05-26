# Changelog

## v0.3.0 -- unreleased

* New sibling product: **Wealth Moments Atlas** (`wealth_moments_atlas_v<v>.csv` /
  `.parquet` / `.manifest.json`) for rows that carry distributional
  moments (mean, median, top shares, negative-wealth share) but no
  headline Gini. Resolves `research_directions.md` item #3
  (previously dropped ~8000 WID country-years).
* Pipeline now emits BOTH atlases on every `wga build`:
  the Gini Atlas (Gini required per row) and the Moments Atlas
  (Gini optional, but at least one other moment required per row).
* `harmonize/national.py::split_gini_and_moments` partitions the
  full harmonized frame into the two products.
* `schema.validate(mode=...)` supports `"gini_atlas"` (default,
  current behavior) and `"moments_atlas"` (Gini may be null;
  flags rows with no moments at all).
* SCF and DFA ingest scaffolds added (`wealth_gini_atlas/ingest/{scf,dfa}.py`):
  documented expected file paths, harmonizer contracts, and stub
  `parse()` that raises `NotImplementedError` until raw files land
  in `data/raw/{scf,dfa}/`. Both sources contribute to the Moments
  Atlas only.
* `.gitignore` updated to allow `data/raw/scf/*.xlsx|csv` and
  `data/raw/dfa/*.zip|csv` through (US Federal Reserve material,
  US public domain).

## v0.2.0 -- unreleased

* HFCS ingest module reads the ECB Statistical Tables XLSX
  workbooks directly. `wga build` auto-detects wave year from
  filenames and extracts Gini / top-5% / top-10% / negative-wealth
  share / mean / median net wealth from sheets J4, F3, A1, A2.
  HFCS does not publish a top-1% share in this workbook, so that
  column remains null in the release.
* Workbooks for waves 1-4 (2010 / 2014 / 2017 / 2021) ship under
  `data/raw/hfcs/` with `.gitignore` exception, so the converter
  is reproducible offline.
* Fallback path: a pre-converted tidy CSV at
  `data/raw/hfcs/hfcs_indicators.csv` (or `WGA_HFCS_LOCAL`)
  remains supported for users who maintain a hand-curated table.
* `harmonize/national.py::from_hfcs` produces household-basis Tier A
  rows with `unit_of_analysis=household`, `comparability_tier=A`,
  `top_tail_flag=survey_only`, and `currency=EUR`.
* Pipeline now stacks WID + HFCS into a single release; same
  country-year may appear under both sources with distinct
  `unit_of_analysis` and `source_dataset` values, preserving the
  natural-key uniqueness invariant.
* Tests: `test_combined_wid_plus_hfcs` for the merge,
  `test_ingest_hfcs_xlsx` for the workbook parser (skips when
  workbooks not present, e.g. sparse clone).
* Resolution semantics: when `WGA_HFCS_LOCAL` (or an explicit
  path) is set, the resolver does *not* fall through to the
  default raw directory -- tests can scope themselves to fixtures.

## v0.1.0

Initial scaffold.

* WID bulk ingest (`wga fetch wid` / `WGA_WID_LOCAL`).
* Release schema with comparability and top-tail metadata.
* Weighted Gini, top/bottom shares, mean and median utilities.
* Negative-wealth zero-out rule for the headline series.
* End-to-end pipeline test against bundled fixtures.
* CI builds a fixture release artifact on every push.

### Hardening (post-scaffold)

* Validator now enforces internal share consistency: `top1 <= top10`,
  `top10 >= 0.10`, `top1 >= 0.01`, `bottom50 <= 0.5`, and
  `top10 + bottom50 <= 1`. Also checks `mean >= median`
  (right-skew of wealth).
* `wga coverage <release>` CLI prints a country x source presence
  matrix for diagnostic use as we layer in HFCS / SCF / DFA.
* Fixtures extended to 5 countries (FR, DE, US, ES, IT) covering
  2010-2020 for a more representative end-to-end test (15 rows).
* `CONTRIBUTING.md` documents how to add a new source, country, or
  variable without breaking the schema.
