# Changelog

## v0.4.0

* **OECD Wealth Distribution ingest** (`ingest/oecd.py`):
  Reads the OECD "WEALTH" SDMX-CSV dataset. `wga fetch oecd` downloads
  automatically; manual fallback documented in module docstring.
  Supplies Gini, top-10%, top-1%, bottom-50%, mean, median for ~30
  OECD countries, filling gaps not covered by HFCS (AU, CA, JP, KR,
  GB, NZ, etc.). `source_priority = "tier2"` so WID/HFCS/LWS tier-1
  rows win when all three overlap.
* **LWS ingest scaffold** (`ingest/lws.py`):
  Three documented access paths (ReShare CSV, LISSY, DART).
  Flexible column normalizer handles both ReShare and custom LISSY
  output layouts, including 0–100 Gini rescaling. `source_priority =
  "tier1"`, `comparability_tier = "A"` -- the gold-standard
  microdata-based series for ~24 countries.
* **`harmonize/iso.py`**: `to_iso3` now accepts ISO-3166-1 alpha-3
  input (OECD, LWS) as well as alpha-2 (WID). Reverse lookup table
  built at import time.
* **US long-run composite series** (`analysis/us_longrun.py` +
  `wga longrun`): Stitches DFA (annual top-1%/top-10%/bottom-50%)
  and SCF (triennial mean/median) into a single analysis-ready annual
  frame 1989–present. Mean/median linearly interpolated to annual
  frequency; raw triennial anchor points preserved as separate columns.
  Cross-check column `top10_gap = DFA - SCF` for methodology drift.
* Pipeline: OECD and LWS slots wired into `build_release`; both skip
  gracefully when source files absent.
* CLI: `wga fetch {oecd,lws}`, `wga longrun [--moments-path] [--out]`.
* `METHOD_VERSION` bumped to `wga-0.4`.

## v0.3.0

* New sibling product: **Wealth Moments Atlas** (`wealth_moments_atlas_v<v>.csv` /
  `.parquet` / `.manifest.json`) for rows that carry distributional
  moments (mean, median, top shares, negative-wealth share) but no
  headline Gini. Resolves `research_directions.md` item #3
  (previously dropped ~8000 WID country-years).
* Pipeline emits BOTH atlases on every `wga build`: the Gini Atlas
  (Gini required per row) and the Moments Atlas (Gini optional, at
  least one other moment required per row).
* `harmonize/national.py::split_gini_and_moments` partitions the
  full harmonized frame into the two products.
* `schema.validate(mode=...)` supports `"gini_atlas"` (default,
  current behavior) and `"moments_atlas"` (Gini may be null; flags
  rows with no moments at all).
* **SCF ingest** (`ingest/scf.py`): reads the interactive chartbook
  CSVs (`interactive_bulletin_charts_all_{mean,median}.csv` and
  `_nwcat_mean.csv`). Produces 12 US triennial rows (1989-2022)
  with mean, median, top-10%, bottom-50% in 2022 USD. Top-10 and
  bottom-50 shares derived from the five nwcat bucket means using
  the fixed SCF population fractions (25/25/25/15/10).
* **DFA ingest** (`ingest/dfa.py`): reads `dfa-networth-shares.csv`,
  Q4 annual snapshot 1989-2025. Produces 37 US rows with top-1%
  (TopPt1 + RemainingTop1), top-10% (adds Next9), and bottom-50%
  shares. Mean / median left null (DFA publishes group-level
  levels only, no per-household denominator).
* Both US sources land in the Moments Atlas as `source_dataset =
  SCF` / `DFA` with `top_tail_flag = survey_only` / `admin_enhanced`
  respectively. They are complementary: SCF supplies mean / median
  that DFA lacks; DFA supplies top-1% that the SCF chartbook
  cannot resolve.
* `.gitignore` allows `data/raw/{scf,dfa}/*.{csv,xlsx,zip,txt}`
  through (US Federal Reserve material, US public domain).
* `METHOD_VERSION` bumped to `wga-0.3`.

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
