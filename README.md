# Wealth Gini Atlas

An open, citable, versioned panel of household **net wealth**
inequality across countries and (eventually) subnational geographies.

The project is **wealth-first**, **harmonization-first**, and
**conservative on definitions, ambitious on packaging**: we ingest
already-authoritative wealth inequality series (WID, OECD, HFCS, SCF,
DFA), map them into a single long-format schema with explicit source
priority and comparability metadata, and publish citable CSV +
Parquet releases.

The project brief lives in `wealth_gini_project_brief.md`; the
methods note in `docs/methods.md`; the codebook in
`docs/codebook.yaml`; and the per-geography source priority in
`docs/source_priority.md`.

## Release roadmap

| Release | Geography                    | Backbone                |
| ------- | ---------------------------- | ----------------------- |
| v0.1    | Global country panel         | WID                     |
| v0.2    | EU country panel             | HFCS + Eurostat + WID   |
| v0.3    | US country + state-aggregate | SCF + DFA               |
| v1.0    | EU NUTS2 + US states         | modeled (Tier C)        |

v0.1 is the only release currently implemented end-to-end.

## Install

```bash
pip install -e ".[dev]"
```

## Build the v0.1 release

The WID bulk download is the upstream source. The pipeline is split
into a fetch step (network) and a build step (offline):

```bash
# 1. Pull WID bulk CSVs into data/raw/wid/
wga fetch wid

# 2. Build the release tables into data/release/
wga build --out-dir data/release

# 3. Sanity-check the artifact against the schema
wga validate data/release/wealth_gini_atlas_v0.1.0.csv

# 4. Inspect coverage (country x source matrix)
wga coverage data/release/wealth_gini_atlas_v0.1.0.parquet
```

If your environment cannot reach `wid.world` directly (sandboxed
runners, restricted networks), download the WID bulk zip on a
machine that can, unzip it, and point `WGA_WID_LOCAL` at the
resulting directory before running `wga build`:

```bash
export WGA_WID_LOCAL=/path/to/unzipped/wid
wga build --out-dir data/release
```

## Run the tests

```bash
pytest
```

The end-to-end test runs the full ingest -> harmonize -> release
pipeline against the bundled fixtures under `data/fixtures/`, so it
does not require network access.

## Schema (release table columns)

See `docs/codebook.yaml` for the machine-readable spec. The key fields
are `geo_id`, `year`, `wealth_concept`, `wealth_gini`,
`top10_wealth_share`, `top1_wealth_share`, `bottom50_wealth_share`,
`mean_net_wealth`, `median_net_wealth`, `unit_of_analysis`,
`source_dataset`, `source_priority`, `comparability_tier`,
`observed_vs_modeled`, `top_tail_flag`, `method_version`.

## License

* Code: MIT (`LICENSE`)
* Release data: CC BY 4.0 (`LICENSE-DATA`)

Upstream sources retain their own licenses; see
`docs/source_priority.md`.

## How to cite

> Wealth Gini Atlas v0.1 (2026). Harmonized panel of household net
> wealth inequality. https://github.com/conway1521/wealth_ineq

A Zenodo DOI will be minted at the v0.1.0 tag.
