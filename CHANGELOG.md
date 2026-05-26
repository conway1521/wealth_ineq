# Changelog

## v0.1.0 -- unreleased

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
