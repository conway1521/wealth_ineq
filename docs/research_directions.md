# Research directions and future extensions

This file is the project's living memo of ideas worth keeping alive
but not yet on the v0.x roadmap. It is curated, not exhaustive.
Entries graduate to `docs/methods.md` or to a release plan once they
have a credible owner and implementation sketch.

The point of this file is to **not lose ideas** between releases.

## 1. Wealth inequality vs wellbeing: empirically testing the policy claim

A lot of contemporary policy talk leans on a chain of inference
that looks roughly like:

    inequality is high  ->  social welfare suffers  ->  policy must reduce inequality

Two reasons that chain is wobblier than it sounds:

* "Inequality" in policy debate almost always defaults to **income**
  inequality (income Gini, growth incidence curves). The empirical
  link between income inequality and aggregate wellbeing measures
  -- life satisfaction, social trust, health outcomes, political
  cohesion -- is contested. (Wilkinson-Pickett "Spirit Level"
  literature on one side; Snowdon, Saunders, others on the other.)
* Wealth inequality and income inequality are not interchangeable.
  Wealth distributions are far more concentrated; mobility through
  wealth is slower; and wealth has direct welfare implications --
  security, opportunity, intergenerational transmission, exposure
  to shocks -- that income flows do not capture. The wealth-welfare
  channel is plausibly *stronger* than the income-welfare channel
  but it is far less measured.

### How the Atlas could be a load-bearing input

The dataset is positioned to be the wealth side of a wealth-vs-
wellbeing empirical agenda. Candidate research questions:

* Do high-wealth-Gini countries score worse on OECD Better Life
  Index pillars after controlling for income Gini? In other words,
  once you partial out income inequality, does wealth inequality
  still bite?
* Does the share of households with negative net wealth predict
  political polarization, institutional trust, or populist vote
  share better than income inequality alone?
* Do regional wealth Ginis (v1.0 NUTS2 / US states) covary with
  health, mortality, or educational outcomes within country, where
  cross-country confounders fall out?
* Does wealth concentration interact with redistributive policy
  outcomes (top-tax-rate persistence, capital-tax base erosion) in
  ways the income-Gini literature misses?

### What this implies for the Atlas design

* Keep the schema merge-ready: stable `geo_id` and `year` keys,
  standard ISO geographies, no in-house geography mangling. The
  current schema already satisfies this.
* Resist the temptation to fold outcome variables (life
  satisfaction, mortality, polarization) into the Atlas. The Atlas
  is *the wealth side*; outcome data lives in a sibling project or
  in user-side merges. Keeping the Atlas focused is what makes it
  useful as an input.
* Eventually publish a worked example: a Quarto / notebook that
  joins the Atlas to OECD BLI and reproduces a wealth-Gini vs
  wellbeing scatter, with the income-Gini partialled out. This is
  good documentation, not core code.

## 2. A Wellbeing Gini -- scoping sketch

The natural sibling product. Wellbeing is multidimensional; income
and wealth are inputs, not the whole picture. There are several
mainstream organizations of the wellbeing dimensions; the SAGE
framework from the Global Solutions Initiative / Bertelsmann
Stiftung "Recoupling Dashboard" is one of the leanest:

* **S**olidarity     -- social cohesion, trust, equal treatment
* **A**gency         -- voice, opportunity, capability
* **G**ain           -- material conditions, income, wealth
* **E**nvironment    -- ecological sustainability, exposure to harms

Adjacent and partially overlapping frameworks worth surveying
before picking a working frame:

* Stiglitz-Sen-Fitoussi Commission report (2009) on measuring
  economic performance and social progress.
* OECD Better Life Index -- 11 dimensions, country-level data
  since 2011.
* UNDP Inequality-adjusted HDI (IHDI) -- *already does Gini-like
  adjustment* on the three HDI dimensions; existence proof that
  the basic computation is reproducible.
* Sen's capability approach and Nussbaum's capability list.
* Bhutan's Gross National Happiness.
* Eurostat "Quality of Life" indicators.

### What a "Wellbeing Gini" could look like

A two-layer product, mirroring how this Atlas is built:

1. **Per-pillar Gini.** For each SAGE pillar (or chosen alternative),
   identify a unit-level distribution within a geography-year and
   compute a Gini-equivalent dispersion measure on it. Examples:
     * Solidarity: dispersion of self-reported social trust (WVS),
       or of inter-group attitudes.
     * Agency: dispersion of educational attainment (PISA, Barro-Lee),
       or of self-reported life-control (Eurobarometer).
     * Gain: dispersion of income / wealth (the existing Atlas
       slots straight in here).
     * Environment: dispersion of exposure to air pollution, of
       access to green space, of climate-disaster vulnerability.
2. **Multidimensional aggregator.** Combine the per-pillar Ginis
   into a composite. Two reasonable approaches:
     * Weighted sum with explicit, justified weights (Atkinson-style
       multidimensional inequality index).
     * Counting / dual-cutoff approach a la Alkire-Foster (used by
       OPHI for the global Multidimensional Poverty Index).

### Why this is plausibly tractable

* The current Atlas already has the schema, validators, source-tier
  framework, release tooling, comparability metadata, and CI. A
  Wellbeing Atlas can reuse the same infrastructure with
  `wealth_concept` replaced by a `pillar` field and a couple of
  new vocabulary entries in `schema.py`.
* The IHDI exists and proves the computation reproduces.
* Pillar-level data are uneven across countries but the coverage
  improves every year (OECD BLI now covers 40+ countries annually).

### Why it might not earn its place

* Index-of-indices products attract permanent
  weights-debate-fatigue and methodological skepticism. The HDI has
  had to defend its 1/3 weights for thirty years.
* If the Wealth Gini Atlas becomes a load-bearing third-party input
  for wellbeing research (per section 1 above), building our own
  composite may be duplicative; better to be the trusted *input*
  than a competing aggregator.
* Source coverage for non-economic pillars is poor outside the
  OECD; a Wellbeing Atlas may force us to a much smaller country
  panel, which would clash with the Wealth Gini Atlas's near-global
  coverage.

### Decision

Deferred until after v0.3 ships. If we pursue it, the first
deliverable should be a scoping memo enumerating:

* Source per SAGE pillar, including coverage matrix.
* A transparent aggregation rule with sensitivity analysis on
  weights.
* A clear non-claim about which frame is "right" -- we publish
  one defensible composite, expose the per-pillar Ginis, and let
  others reweight.

## 3. Moments-only rows from WID (currently dropped)

The v0.1 build drops ~8,000 WID country-year rows where a top
share or a mean is published without a Gini. The strict reading is
that this is a Wealth *Gini* Atlas. The looser reading is that the
brief also requires "companion variables for macro relevance"
(mean, top10, top1, bottom50) and that those rows carry signal
even without a headline Gini.

The macro / heterogeneous-agent literature in particular often
needs moments other than the Gini -- the Saez-Zucman, Kaymak-Poschke,
and Krueger-Mitman-Perri papers all rely on top-1% and bottom-50%
shares as primary calibration targets, with the Gini as secondary.

Options for v0.3 or v0.4:

* **Companion table.** Add `wealth_moments_atlas_v0.X.csv` with the
  moments-only rows under the same schema (Gini allowed to be
  null). Cleanly separated from the headline Gini product;
  preserves the headline framing.
* **Loosened main schema.** Reintroduce these rows into the main
  release with a flag column (`headline_complete = false`).
  Messier schema, easier downstream merge.

The companion-table approach is the lower-risk default. No action
needed before user demand surfaces, but the rows are easy to
recover -- they live in `data/raw/wid/` and the parser already
knows how to find them; just remove the `dropna(subset=["wealth_gini"])`
in `harmonize/national.py` and route to a separate writer.

## 4. Top-tail correction flags (Saez-Zucman style)

Currently every WID row carries `top_tail_flag = "mixed"` because
WID's per-country pipelines combine survey and administrative
inputs heterogeneously. The honest version of this column would
distinguish:

* Pure survey-based estimates (HFCS, raw SCF).
* Estimates that incorporate Saez-Zucman-style **capitalization
  of investment-income flows** to recover top wealth.
* Estimates that incorporate **estate-multiplier** methods.
* Estimates that incorporate **wealth tax** administrative records
  (Norway, Sweden, Spain, Switzerland).

A v0.5 enhancement could populate this column from WID's per-country
metadata files (`WID_metadata_<ISO2>.csv`), which document exactly
which inputs the country team used. The metadata is already on
disk after `wga fetch wid`; we just don't parse it yet.

Why this matters: the survey-vs-admin distinction is the single
biggest comparability fault line in the wealth-inequality
literature. A column that flags it honestly is the highest-value
methodological add for the smallest amount of code.

## Stewardship rule

Add an entry here whenever the user, a contributor, or a reviewer
raises a direction worth keeping alive. Keep entries tight: one
section, the question, why it might matter, why it might not, what
the next step would be.

Promote an entry out of this file when:

* It earns a milestone in `CHANGELOG.md` (becomes a release).
* It earns a methodology section in `docs/methods.md` (becomes
  part of the standard).
* The team decides not to pursue it (move to an `archived/`
  subsection at the bottom of this file with a one-line reason
  -- do not delete; preserving rejected ideas avoids re-litigating).
