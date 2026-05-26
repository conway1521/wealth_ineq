# Wealth Gini Atlas: Project Brief, Methods, and Design Principles

## Overview

This document sets out a proposed open, citable, and extensible dataset project focused on wealth inequality across countries and subnational geographies. The project is designed to produce a standardized **Wealth Gini Atlas** that begins with nationally comparable country-year data and then expands into European regional geographies such as NUTS 2 and U.S. state-level estimates where the underlying data quality supports that extension.[cite:35][cite:34][cite:24][cite:50]

The central idea is not to reinvent the measurement of wealth from first principles. Instead, the project builds on established statistical and research traditions from the OECD, Eurostat, the World Inequality Database, the Survey of Consumer Finances, and related macro-distributional work associated with researchers such as Gabriel Zucman and Emmanuel Saez.[cite:70][cite:78][cite:35][cite:24][cite:64][cite:67]

The intended product is both a research dataset and a public-facing source. It is meant to be useful enough for researchers to merge directly into empirical work, transparent enough for others to audit and extend, and simple enough to remain maintainable over time.[cite:70][cite:77][cite:35]

## Purpose

The project aims to solve a practical gap in the current inequality data ecosystem. There are strong resources for income inequality and important sources for wealth inequality, but there is no single, simple, open, well-documented panel that gives users a harmonized entry point to wealth Gini estimates across global national units and selected subnational layers.[cite:9][cite:35][cite:12][cite:34][cite:50]

The proposed dataset is therefore meant to be additive in five ways:[cite:35][cite:70][cite:77]

- It is **wealth-first**, whereas many widely used Gini datasets are income-first.[cite:9][cite:35]
- It is designed as a **joinable panel dataset**, with stable identifiers, tidy structure, and explicit versioning.[cite:35][cite:70]
- It includes a **comparability framework** rather than implying all sources are equally comparable.[cite:34][cite:70]
- It is intended to support both **empirical inequality research** and **macro / micro-macro applications** by including companion distributional variables beyond the Gini alone.[cite:64][cite:67][cite:77]
- It creates a path from a tractable first release to more original regional and subnational extensions without overclaiming precision where source data are weak.[cite:24][cite:34][cite:49]

## Who This Is For

The dataset is designed for several overlapping audiences.[cite:70][cite:77][cite:35]

### Academic researchers

Applied economists, inequality researchers, political economists, and labor market scholars need a simple, transparent wealth inequality series that can be merged into cross-country or panel research without rebuilding a data pipeline from scratch.[cite:35][cite:70][cite:77]

### Macro and micro-macro researchers

Modern macroeconomics and heterogeneous-agent research increasingly need distributional moments, not just aggregate household balance-sheet totals. A harmonized wealth Gini panel with top and bottom wealth shares, mean wealth, and clear links to official wealth concepts is therefore directly useful for calibration, descriptive trend analysis, and empirical validation.[cite:64][cite:65][cite:67][cite:77][cite:78]

### Public policy and institutional users

Public institutions, think tanks, and central-bank-adjacent researchers often need usable wealth inequality measures that align with official definitions and can be discussed without extensive methodological translation. Grounding the project in OECD, Eurostat, SCF, and WID conventions makes it easier for institutional users to trust and adopt.[cite:70][cite:78][cite:24][cite:35]

### Data journalists and open-data users

A simple country-year or region-year file with clean metadata, source flags, and clear caveats can serve journalists, public-interest researchers, and secondary data users who need a defensible measure without navigating multiple source systems.[cite:35][cite:12][cite:50]

## Core Design Choice

The project should be conservative in definitions and ambitious in packaging, integration, and transparency. The innovation is not a novel inequality functional form. The innovation is the creation of a consistent, openly documented, geographically extensible wealth inequality resource that others can cite, replicate, and build on.[cite:70][cite:35][cite:77]

This means the project should adopt official or near-official definitions of wealth where possible, use a standard Gini approach, and reserve methodological originality for harmonization, source mapping, metadata design, and carefully labeled subnational estimation.[cite:70][cite:78][cite:64][cite:67]

## Scope and Release Strategy

A staged release strategy is the most tractable path.[cite:35][cite:24][cite:34][cite:50]

| Release stage | Geography | Likely backbone | Rationale |
|---|---|---|---|
| v0.1 | Global country-year panel | WID wealth inequality series [cite:35] | Fastest route to a useful, citable, wealth-first panel [cite:35] |
| v0.2 | EU country-year panel | HFCS, Eurostat, WID [cite:34][cite:78][cite:35] | Stronger cross-country comparability within Europe [cite:34][cite:78] |
| v0.3 | U.S. national panel | SCF and DFA [cite:24][cite:50] | Strong wealth measurement and time-series relevance [cite:24][cite:50] |
| v1.0 experimental | EU regional and U.S. state estimates | Mixed survey, accounts, and modeled inputs [cite:34][cite:24][cite:49] | Distinctive contribution, but should be clearly labeled experimental [cite:34][cite:24][cite:49] |

This sequencing reflects the fact that global national data are currently much more feasible than truly comparable subnational wealth panels across the U.S. and EU.[cite:35][cite:34][cite:24]

## Sources and Source Hierarchy

The project should use a formal source hierarchy rather than pooling all sources on equal terms.[cite:35][cite:70][cite:50]

### Tier 1: Preferred backbone sources

- **World Inequality Database (WID):** preferred starting point for national wealth inequality series and wealth Gini availability where already published.[cite:35]
- **OECD household wealth standards and wealth-distribution publications:** preferred definitional backbone for household wealth concepts and internationally comparable micro-statistics.[cite:70][cite:77]
- **Eurostat and HFCS:** preferred European household wealth architecture, especially for EU consistency and financial asset/liability categorization.[cite:34][cite:78]
- **Survey of Consumer Finances (SCF):** preferred U.S. microdata benchmark for household wealth levels and distributions.[cite:24][cite:26]
- **Distributional Financial Accounts (DFA):** preferred U.S. national time-series complement linking aggregate financial accounts and distributional breakdowns.[cite:50][cite:41]

### Tier 2: Supporting and contextual sources

- National statistical offices and central bank household wealth sources where these align with OECD-style definitions.[cite:70][cite:78]
- OECD and related wealth-distribution publications for cross-checking shares and interpretive context.[cite:77][cite:69]
- Research syntheses on global wealth inequality and top-tail measurement.[cite:65][cite:66][cite:64][cite:67]

### Source priority rule

Where an authoritative wealth inequality series already exists in WID or a directly comparable official source, the project should ingest and document that series rather than reconstructing it from scratch. Original estimation should be reserved for settings where there is a real gap and the method can be defended transparently.[cite:35][cite:70][cite:66]

## Conceptual Definition of Wealth

The headline measure should be based on **net household wealth** defined as total household assets minus total household liabilities, following OECD-style household wealth concepts and closely aligned European financial assets and liabilities frameworks.[cite:70][cite:78]

### Headline concept

**Net household wealth** should include the broadest feasible set of assets and liabilities available in the source data:[cite:70][cite:78][cite:77]

- Financial assets, such as deposits, bonds, listed and unlisted equity, mutual fund shares, retirement assets, and insurance or pension claims where measured.[cite:70][cite:78]
- Non-financial assets, especially owner-occupied housing, other real estate, and business assets where measured.[cite:70][cite:78]
- Liabilities, including mortgages, consumer credit, and other household debts.[cite:70][cite:78]

### Supplementary variants

To support richer analysis without fragmenting the main product, the project can also publish supplementary wealth concepts where sources allow:[cite:70][cite:78]

- Net financial wealth.[cite:78]
- Net housing or real-estate wealth.[cite:70][cite:78]
- Total non-financial wealth.[cite:70]

The main public-facing index should remain one clear headline concept rather than multiple competing “main” measures.[cite:70][cite:77]

## Why the Headline Measure Should Stay Simple

Wealth data become difficult very quickly if the project tries to solve every conceptual issue at once. The tractable strategy is therefore to fix one headline measure, publish a small number of supplementary variants, and let the metadata carry the complexity.[cite:70][cite:35]

This approach preserves usability. Researchers can cite one flagship series, while more advanced users can inspect the component coverage, exclusions, and comparability fields for a given observation.[cite:35][cite:70]

## Unit of Analysis

The underlying surveys most relevant to the project are household-based, especially SCF and HFCS.[cite:24][cite:34] For public release, the project should define a primary unit of analysis explicitly and store it in metadata so users know what each Gini represents.[cite:70][cite:34]

A practical baseline is to compute the headline series at the **household** level where that is what the source directly supports, while also leaving room for a later per-adult or adult-equivalent series if a strong harmonization case emerges. Eurostat’s broader inequality practice underscores the value of equivalization in some contexts, but forcing equivalized wealth into the first release could create more friction than value.[cite:61][cite:70]

The release file should therefore include:

- `unit_of_analysis`
- `equivalence_scale`
- `population_basis`

This keeps the design extensible without overcomplicating the initial release.[cite:70][cite:34]

## Gini Calculation Standard

The project should use the standard Gini coefficient as the headline inequality measure. That aligns with broad statistical practice and maximizes interpretability for downstream users.[cite:55][cite:57][cite:13]

The ordinary Gini logic is the same as in income applications: it measures average pairwise dispersion relative to the mean distributional level.[cite:55][cite:57] The challenge in wealth applications is not the formula itself but the treatment of zero and negative net wealth values, which are common in household balance-sheet data.[cite:55][cite:30]

### Negative wealth rule

A key methodological choice is needed because wealth distributions often include households with debts greater than assets. Our World in Data notes that applying the Gini directly to distributions that contain negative values can produce values above 1, which are awkward to interpret in standard inequality terms.[cite:55]

For tractability and interpretability, the recommended public standard is:

- Construct the net wealth variable at the chosen unit of analysis.[cite:70][cite:78]
- Set negative net wealth values to zero for the **headline public wealth Gini**.[cite:55]
- Publish separate companion variables for the share of units with negative net wealth and the share with zero or non-positive net wealth.[cite:55][cite:77]

This preserves a simple 0 to 1-style Gini interpretation while retaining important information about indebtedness and wealth fragility.[cite:55]

### Computational formula

For a sorted non-negative distribution, the standard computational Gini formula can be used:[cite:55]

\[
G = \frac{\sum_{i=1}^{n}(2i-n-1)x_i}{n\sum_{i=1}^{n}x_i}
\]

This classical formulation is appropriate because the project’s contribution lies in building, harmonizing, and documenting the wealth variable rather than inventing a new inequality index.[cite:55][cite:70]

## Companion Variables for Macro Relevance

To make the dataset useful to modern macroeconomics and micro-macro research, the file should not stop at a single Gini number.[cite:64][cite:65][cite:67][cite:77]

Where the source permits, each observation should also include:

- Mean net wealth.[cite:77][cite:78]
- Median net wealth.[cite:77]
- Top 10 percent wealth share.[cite:77][cite:69]
- Top 1 percent wealth share where available.[cite:64][cite:67]
- Bottom 50 percent wealth share where available.[cite:64][cite:77]
- Negative-wealth share.[cite:55]
- Source and method flags.[cite:35][cite:70]

This mirrors the fact that leading macro-distributional work often relies on multiple moments of the wealth distribution, not just one summary measure.[cite:64][cite:65][cite:67]

## Relationship to Saez, Zucman, and Modern Wealth Research

The project should borrow from the **spirit** of modern wealth-distribution research without taking on every technical burden of those research programs. Saez and Zucman’s major contribution was not a new Gini formula; it was the use of tax, administrative, and capitalization methods to recover a more accurate wealth distribution, especially at the top tail where household surveys often understate concentration.[cite:64][cite:67][cite:72]

That insight matters for this project in three ways.[cite:64][cite:67][cite:66]

### First, top-tail humility

When the data source is survey-only, the project should explicitly acknowledge that top wealth concentration may be understated relative to admin-enhanced series.[cite:64][cite:66][cite:67] This is not a flaw if it is documented clearly. It becomes a flaw only if the product suggests survey-based and admin-enhanced estimates are directly interchangeable without qualification.[cite:66][cite:70]

### Second, source-aware hierarchy

If WID or an official national series has already incorporated richer estimation methods, the project should prefer those published values over de novo reconstruction whenever that yields a more credible national estimate.[cite:35][cite:66][cite:65]

### Third, future extensibility

The project should leave room for future top-tail correction flags, capture-quality indicators, or preferred-series designations. Those additions would let users distinguish between pure survey estimates and estimates influenced by admin or capitalization methods.[cite:66][cite:67][cite:70]

## Comparability Framework

Comparability is one of the project’s main value propositions, but it should be handled honestly. “Comparable” should mean harmonized enough for responsible use, with documented caveats, not falsely identical across all countries, years, and geographies.[cite:34][cite:70][cite:35]

The dataset should therefore include a **comparability tier** for each observation.[cite:70][cite:34]

| Tier | Meaning | Typical example |
|---|---|---|
| A | Same survey family or strongly harmonized wealth concept [cite:34][cite:70] | HFCS-based EU observations with consistent household wealth definitions [cite:34][cite:70] |
| B | Same broad wealth concept, but differing source machinery [cite:35][cite:70] | WID-based national estimates built from different country inputs [cite:35] |
| C | Modeled, inferred, or partially synthetic estimate [cite:24][cite:49][cite:50] | Experimental subnational state or NUTS2 estimate not directly observed in a harmonized survey [cite:24][cite:49] |

This turns a potential weakness into a product feature. Users gain a transparent way to filter the data for stricter or looser research standards.[cite:70][cite:35]

## Subnational Strategy

The project’s most distinctive long-run contribution may be subnational wealth inequality, especially U.S. states and European regions such as NUTS 2. However, these layers should be treated as a second-order extension, not as the basis of the first public release.[cite:24][cite:34][cite:49]

### EU regional layer

The search landscape suggests that HFCS and Eurostat provide strong national and household wealth architecture for Europe, but a ready-made, open, EU-wide NUTS2 wealth inequality panel is not straightforwardly available.[cite:34][cite:49][cite:78] That means any NUTS2 extension is likely to involve significant original estimation or indirect regionalization and must therefore be labeled accordingly.[cite:34][cite:49]

### U.S. state layer

SCF is the benchmark for U.S. household wealth, but it is not a canonical state-by-state wealth inequality panel.[cite:24][cite:26] The DFA provides strong national time-series context, but not a direct state panel of household wealth inequality.[cite:50][cite:41] A U.S. state series is therefore possible only as a modeled or hybrid layer unless a stronger subnational source is identified.[cite:24][cite:50]

### Implication

The right framing is that the project begins with a high-confidence national layer and later adds experimental subnational layers under explicit methodological labeling.[cite:35][cite:24][cite:34]

## Data Model and Schema

The public release should use a tidy long-format schema. Each row should represent a geography-year-observation combination, and each variable should be clearly defined in a machine-readable codebook.[cite:35][cite:70]

### Minimum schema

- `geo_id`
- `geo_name`
- `geo_level`
- `year`
- `wealth_concept`
- `wealth_gini`
- `negative_wealth_share`
- `mean_net_wealth`
- `median_net_wealth`
- `top10_wealth_share`
- `top1_wealth_share`
- `bottom50_wealth_share`
- `unit_of_analysis`
- `equivalence_scale`
- `source_dataset`
- `source_priority`
- `comparability_tier`
- `observed_vs_modeled`
- `top_tail_flag`
- `method_version`
- `notes`

### Geography standards

The project should use standard geographic identifiers wherever possible, including ISO country codes and NUTS codes for Europe.[cite:49][cite:78] U.S. identifiers should be standardized as well, whether via FIPS, ANSI, or a clearly documented alternative.[cite:24]

This design makes the dataset easy to merge into other macro, demographic, labor market, or political datasets.[cite:70][cite:77]

## Maintenance and Open-Source Strategy

To be citable and useful, the project should be released as an open, versioned repository with a stable DOI workflow and transparent update log.[cite:35][cite:70]

### Recommended infrastructure

- GitHub repository for data files, code, documentation, and issues.
- Tagged releases with semantic versioning.
- Zenodo integration for DOI-minted releases.
- Plain CSV and Parquet outputs.
- A concise methods note and a longer technical documentation file.

### Reproducibility principle

Where licensing permits, the repository should include the code that transforms upstream sources into the public release tables. Where full redistribution is not possible, the repository should at least include a documented extraction and transformation recipe.[cite:34][cite:70][cite:24]

The project should err on the side of reproducibility, but not at the cost of violating source licenses or access rules.[cite:34][cite:70]

## Why This Is Additive

The project is additive because it lowers the transaction cost of wealth inequality research without asking users to abandon existing trusted sources.[cite:35][cite:70][cite:77] It acts as a standardized interface layer across sources that are already influential but not always easy to combine, interpret, or cite as one coherent product.[cite:35][cite:34][cite:24][cite:50]

Its contribution is especially strong in the following areas:[cite:35][cite:70][cite:77]

- Converting source complexity into a **usable research panel**.[cite:35]
- Creating one **wealth-first entry point** for users who are currently pushed toward income inequality resources.[cite:9][cite:35]
- Making **comparability explicit** rather than assumed.[cite:34][cite:70]
- Designing for both **empirical researchers** and **macro model users** through companion variables and method flags.[cite:64][cite:67][cite:77]
- Providing a credible path toward **regional wealth inequality products** that are clearly labeled by confidence level.[cite:24][cite:34][cite:49]

## Why This Is Tractable

The project is tractable because its first release can rely heavily on already existing published infrastructure rather than full original estimation.[cite:35][cite:24][cite:34] WID already provides wealth inequality content, OECD already provides internationally recognized wealth-statistics definitions, Eurostat and HFCS already provide a European statistical backbone, and SCF plus DFA already provide a strong U.S. wealth basis.[cite:35][cite:70][cite:34][cite:24][cite:50]

This means the first release can succeed as a high-quality harmonization and documentation exercise even before any ambitious subnational modeling begins.[cite:35][cite:70]

## Design Principles

The project should follow a clear set of design principles.[cite:70][cite:35][cite:77]

### Principle 1: Official where possible

Use official or quasi-official concepts and published research series where available instead of recreating them.[cite:70][cite:35]

### Principle 2: One headline measure, several supporting measures

Keep the public-facing product simple, but publish supporting variables that make the dataset more analytically powerful.[cite:55][cite:77]

### Principle 3: Transparency over false precision

Document differences across sources, carry comparability metadata, and do not imply stronger comparability than the data can support.[cite:34][cite:70]

### Principle 4: Survey-aware, top-tail-aware

Recognize that household survey wealth data can understate top concentration and indicate whether observations are survey-only or informed by richer estimation traditions.[cite:64][cite:66][cite:67]

### Principle 5: Built for research use

Use stable IDs, consistent naming, long-format files, and merge-ready conventions so the data are easy to integrate into empirical work.[cite:35][cite:70]

### Principle 6: Extensible by design

Allow future additions such as per-adult variants, top-tail adjustments, regional layers, and alternative wealth concepts without breaking the core structure.[cite:70][cite:34][cite:24]

## Suggested Public Framing

A useful public framing would be that the project is an **open wealth inequality atlas** or **wealth Gini atlas** that translates the best available official and research data into a citable, transparent, and extensible panel resource.[cite:35][cite:70][cite:77]

That framing is credible because it does not overclaim methodological novelty while still highlighting a real gap in how wealth inequality data are currently organized and used.[cite:35][cite:70]

## Suggested Core Statement

A concise project statement could read as follows:

> The Wealth Gini Atlas is an open, versioned dataset that harmonizes the best available national and subnational measures of household net wealth inequality across countries and regions. It is grounded in OECD and Eurostat wealth definitions, incorporates published inequality series from sources such as WID, SCF, and DFA where available, and provides transparent metadata on comparability, source quality, and methodological scope.[cite:70][cite:78][cite:35][cite:24][cite:50]

## Working Bibliography

The following source list is included as a practical bibliography for project development. Unlike the inline citations above, this list is meant to help guide implementation work.

- World Inequality Database. “Gini coefficients available.” WID news post and related wealth inequality resources.[cite:35]
- OECD. *Guidelines for Micro Statistics on Household Wealth*.[cite:70]
- OECD. *Society at a Glance 2024*, chapter on income and wealth inequalities.[cite:77]
- Eurostat. Household Finance and Consumption Survey portal.[cite:34]
- Eurostat. Statistics on household financial assets and liabilities.[cite:78]
- Federal Reserve Board. Survey of Consumer Finances portal and data visualization materials.[cite:24][cite:26]
- Federal Reserve Board. Distributional Financial Accounts overview and related visualization material.[cite:50][cite:41]
- Saez, Emmanuel, and Gabriel Zucman. “Wealth Inequality in the United States since 1913.”[cite:67]
- Saez, Emmanuel, and Gabriel Zucman. “The Rise of Income and Wealth Inequality in America.”[cite:64][cite:68]
- Annual Review of Economics. “Global Wealth Inequality.”[cite:65]
- Stone Center / related archive. “Methods of Estimation of Wealth Inequality.”[cite:66]
- Our World in Data. “Measuring inequality: what is the Gini coefficient?”[cite:55]

## Immediate Next Steps

The most practical next step is to turn this brief into a repository specification and methods memo.[cite:35][cite:70][cite:34] That would include a draft schema file, a source-priority table by geography, a written negative-wealth handling standard, and a first-pass country coverage matrix for the v0.1 global release.[cite:35][cite:55][cite:34]

A second near-term step would be to define which observations will be treated as directly observed, which will be imported from published wealth inequality series, and which will eventually require modeled estimation.[cite:35][cite:24][cite:34][cite:50] That distinction should be locked in early because it determines the credibility of every downstream subnational expansion.[cite:70][cite:66]
