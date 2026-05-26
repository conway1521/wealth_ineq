# Methods note -- Wealth Gini Atlas v0.1

This memo summarizes the methodological choices baked into the v0.1
release. It is the public-facing operationalization of the project
brief in the repository root.

## 1. Wealth concept

The headline measure is **net household wealth**: total household
assets minus total household liabilities, following OECD-style
guidelines for micro statistics on household wealth. Where the source
publishes only narrower variants (net financial wealth, net housing
wealth), we either rely on its broader composite or flag the row as
not directly comparable.

v0.1 publishes only the headline `wealth_concept = net_wealth`. v0.2
will introduce the supplementary variants alongside the headline.

## 2. Unit of analysis

WID publishes its wealth series on a **per-adult equal-split** basis:
each adult is attributed an equal share of their household's wealth.
We carry this convention through v0.1 by setting
`unit_of_analysis = per_adult_equal_split`. HFCS and SCF native units
are the **household**; both will appear in v0.2 / v0.3 alongside the
per-adult WID rows. The release is therefore long-format with multiple
unit bases per (geo_id, year), distinguished by `unit_of_analysis`.

## 3. Gini computation and negative wealth

Wealth distributions routinely contain units with negative net wealth
(debts above assets). The textbook Gini formula applied to a
distribution with negative values can exceed 1, which breaks the
familiar [0, 1] interpretation.

**Public standard.** The headline `wealth_gini` is computed after
setting negative net-wealth observations to zero. The share of units
with negative net wealth is stored separately as
`negative_wealth_share`. We also expose the raw Gini (before
zero-out) as `wealth_gini_raw` for users who want to work with the
unmodified statistic.

For WID-imported rows the published Gini is *intended* to respect
[0, 1] by construction (WID handles negatives at the micro level
before computing the Gini). In practice a small number of highly
unequal country-years have published WID Ginis slightly above 1.0 --
South Africa over 1910-2012 is the prominent case in the v0.1
backbone -- because residual negative wealth in the bottom tail
survives WID's own treatment.

**Clipping rule for source-imported Ginis.** We clip the headline
`wealth_gini` to [0, 1] so downstream users keep the familiar
invariant. The unclipped source value is preserved in
`wealth_gini_raw`, and the clip is logged in `notes`
(`"headline clipped from <value> to [0,1]"`). Values that fall more
than 0.10 outside the unit interval are treated as anomalies and
dropped from the headline column (the raw value is still recorded);
this defends against future WID format changes or sentinel values
that would otherwise corrupt the public series.

## 4. Source hierarchy

| Tier   | Source              | Used as                                        |
| ------ | ------------------- | ---------------------------------------------- |
| tier1  | WID                 | v0.1 global national backbone                   |
| tier1  | HFCS + Eurostat     | v0.2 EU national + harmonized household basis  |
| tier1  | SCF                 | v0.3 US national household-basis benchmark     |
| tier1  | DFA                 | v0.3 US quarterly admin-anchored top shares    |
| tier2  | National statistics | cross-checks and gap fills                     |

We do not pool sources on equal terms. Where multiple sources publish
the same country-year, we keep all rows (different
`source_dataset` values) and let downstream users filter by source
and `comparability_tier`.

## 5. Comparability tiers

* **Tier A**: same survey family, strongly harmonized concept
  (HFCS in the euro area).
* **Tier B**: same broad wealth concept, different source machinery
  (WID's national series).
* **Tier C**: modeled, inferred, or partially synthetic
  (NUTS2 and US state rows in v1.0).

All v0.1 rows are Tier B (`source_dataset = WID`).

## 6. Top-tail honesty

Survey-only wealth estimates tend to understate top concentration
relative to estimates that incorporate tax microdata or capitalization
of investment-income flows (Saez and Zucman, 2016; Saez and Zucman,
2020). We do not "correct" the published series in this release.
Instead, every row carries a `top_tail_flag`:

* `survey_only`     -- pure survey, top understated risk.
* `admin_enhanced`  -- top tail built from admin/capitalization work.
* `mixed`           -- blended (WID country files often combine inputs).
* `unknown`         -- documentation insufficient to classify.

## 7. Currency and price basis

Wealth levels (`mean_net_wealth`, `median_net_wealth`) are stored in
the `currency` column's units. WID rows use EUR purchasing-power
parity, the WID reference unit. SCF and DFA rows will use current
USD; HFCS rows will use current EUR. Cross-country level comparisons
should restrict to a single currency basis.

## 8. Reproducibility

`make data-wid` (or `wga fetch wid` then `wga build`) produces the
v0.1 release tables from a fresh WID bulk download. The repository
ships fixture CSVs under `data/fixtures/` so the full pipeline can
be exercised offline; `pytest` runs the end-to-end test against
those fixtures.

## 9. What this release does NOT claim

* No new Gini formula. The contribution is harmonization, schema, and
  metadata, not a new inequality functional form.
* No subnational coverage. NUTS2 and US state series ship as
  `comparability_tier = "C"` in v1.0, clearly labeled as
  experimental.
* No claim that survey and admin-enhanced top shares are
  interchangeable. The `top_tail_flag` is the user's tool for
  filtering.
