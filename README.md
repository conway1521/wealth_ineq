# Wealth Gini Atlas

An open, citable, versioned panel of household **net wealth inequality** across
countries and (eventually) subnational geographies.

**v0.4.0** · 10,783 rows · 213 countries · 1800-2025 · CC BY 4.0

The project is wealth-first, harmonization-first, and conservative on definitions:
we ingest already-authoritative wealth inequality series (WID, HFCS, SCF, DFA, LWS),
map them into a single long-format schema with explicit source priority and
comparability metadata, and publish citable CSV + Parquet releases.

Companion product: the **Wealth Moments Atlas** (7,923 rows · 53 countries) ships
alongside and contains distributional moments (top shares, mean, median) for rows
where no headline Gini is available, useful for macro/HANK calibration.

## Documentation

| File | Contents |
|------|----------|
| [`docs/methods.md`](docs/methods.md) | Methodology and design choices |
| [`docs/codebook.yaml`](docs/codebook.yaml) | Machine-readable column definitions |
| [`docs/source_priority.md`](docs/source_priority.md) | Source hierarchy by geography |
| [`docs/research_directions.md`](docs/research_directions.md) | Future extensions and research ideas |
| [`wealth_gini_project_brief.md`](wealth_gini_project_brief.md) | Original project brief |

## Data sources

| Source | Type | Geography | Unit | Tier | Comparability |
|--------|------|-----------|------|------|--------------|
| WID | Admin-survey blend | Global (213 countries) | Per-adult equal-split | tier1 | B |
| HFCS | Harmonized survey | Euro area (20 countries) | Household | tier1 | A |
| LWS | Harmonized survey | 24 OECD countries | Household | tier1 | A |
| SCF | Survey | United States | Household | tier1 | A |
| DFA | Admin-anchored | United States | Household | tier1 | A/B |
| OECD | Published indicators | OECD members | Household | tier2 | B |

## Release roadmap

| Release | Geography | Backbone | Status |
|---------|-----------|----------|--------|
| v0.1 | Global country panel | WID | shipped |
| v0.2 | EU country panel | HFCS + WID | shipped |
| v0.3 | US national + moments | SCF + DFA | shipped |
| v0.4 | OECD + LWS + US long-run | LWS + OECD | shipped |
| v1.0 | EU NUTS2 + US states | modeled (Tier C) | planned |

## Install

```bash
pip install -e ".[dev]"
```

## Build the release

```bash
# 1. Pull WID bulk CSVs into data/raw/wid/ (requires network to wid.world)
wga fetch wid

# 2. Build both release products into data/release/
wga build --out-dir data/release

# 3. Build the US long-run composite (reads the Moments Atlas parquet)
wga longrun --out data/release/us_longrun.csv

# 4. Validate the Gini Atlas
wga validate data/release/wealth_gini_atlas_v0.4.0.csv
```

### Optional additional sources

```bash
# OECD wealth distribution data (fetches via SDMX API)
wga fetch oecd

# LWS (Luxembourg Wealth Study), download Gini_LWS.dta from ReShare
# and place it in data/raw/lws/ before running wga build
# https://reshare.ukdataservice.ac.uk/855655/
```

If your environment cannot reach `wid.world`, download the WID bulk zip separately,
unzip it, and point `WGA_WID_LOCAL` at the directory:

```bash
export WGA_WID_LOCAL=/path/to/unzipped/wid
wga build --out-dir data/release
```

## Run the tests

```bash
pytest
```

The test suite runs the full ingest → harmonize → release pipeline against bundled
fixture data; no network access required. 60 tests pass.

## Schema

See [`docs/codebook.yaml`](docs/codebook.yaml) for the machine-readable spec.
Key fields: `geo_id`, `year`, `wealth_concept`, `wealth_gini`, `top10_wealth_share`,
`top1_wealth_share`, `bottom50_wealth_share`, `mean_net_wealth`, `median_net_wealth`,
`unit_of_analysis`, `source_dataset`, `source_priority`, `comparability_tier`,
`observed_vs_modeled`, `top_tail_flag`, `method_version`.

Both release products share the same schema; `wealth_gini` is non-null in the Gini
Atlas and nullable in the Moments Atlas.

## Download

Release artifacts live under [`data/release/`](data/release/).

| File | Format | Size |
|------|--------|------|
| `wealth_gini_atlas_v0.4.0.csv` | CSV | 2.6 MB |
| `wealth_gini_atlas_v0.4.0.parquet` | Parquet | 233 KB |
| `wealth_moments_atlas_v0.4.0.csv` | CSV | 1.1 MB |
| `wealth_moments_atlas_v0.4.0.parquet` | Parquet | 74 KB |
| `us_longrun.csv` | CSV | - |

## License

* Code: MIT ([`LICENSE`](LICENSE))
* Release data: CC BY 4.0 ([`LICENSE-DATA`](LICENSE-DATA))

Upstream sources retain their own licenses; see [`docs/source_priority.md`](docs/source_priority.md).

## How to cite

> Wealth Gini Atlas v0.4.0 (2026). Harmonized panel of household net wealth
> inequality. https://github.com/conway1521/wealth_ineq

A Zenodo DOI will be minted at the v1.0 release.
