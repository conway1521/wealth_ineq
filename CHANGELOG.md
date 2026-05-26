# Changelog

## v0.2.0 -- unreleased

* HFCS ingest module (`wga fetch hfcs`) reading a tidy CSV from
  `data/raw/hfcs/hfcs_indicators.csv` (or `WGA_HFCS_LOCAL`). The
  expected schema is documented in `wealth_gini_atlas/ingest/hfcs.py`
  and a synthetic fixture for DE/FR/IT/ES across waves 1-4 ships under
  `data/fixtures/hfcs_indicators.csv`.
* `harmonize/national.py::from_hfcs` produces household-basis Tier A
  rows with `unit_of_analysis=household`, `comparability_tier=A`,
  `top_tail_flag=survey_only`, and `currency=EUR`.
* Pipeline now stacks WID + HFCS into a single release; same
  country-year may appear under both sources with distinct
  `unit_of_analysis` and `source_dataset` values, preserving the
  natural-key uniqueness invariant.
* End-to-end test `test_combined_wid_plus_hfcs` covers the two-source
  merge, schema validation, and the per-source metadata invariants.

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
