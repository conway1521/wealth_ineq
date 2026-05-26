# Source priority by geography

This table records which source we treat as the **primary backbone**
for each geographic layer, plus the source we use for cross-checks.
The primary backbone fills the `wealth_gini` headline for that
geography; supporting sources are added as additional rows in the
release file with their own `source_dataset` value so users can
compare or filter.

| Geography                 | Primary backbone | Supporting sources                    | Tier  |
| ------------------------- | ---------------- | ------------------------------------- | ----- |
| Global country panel      | WID              | OECD WDD, national stats offices      | B     |
| Euro-area countries       | HFCS             | WID, Eurostat sector accounts         | A     |
| Non-euro EU countries     | WID              | HFCS where available, Eurostat        | B     |
| United States (national)  | SCF + DFA        | WID, Saez-Zucman series               | A / B |
| EU NUTS2 regions          | modeled          | HFCS regional flags, regional accts.  | C     |
| US states                 | modeled          | SCF + ACS regressors, DFA totals      | C     |

## Source priority rule

If WID or another authoritative series already publishes a wealth Gini
for a (geo, year) cell, we ingest it verbatim rather than recompute.
We reserve original estimation for cells with a real gap, and we mark
those cells as `observed_vs_modeled = "modeled"` with a clear
`method_version`.

This keeps v0.1 a high-quality harmonization product. Genuinely
original estimation is concentrated in v1.0 subnational rows where
no published harmonized series exists.
