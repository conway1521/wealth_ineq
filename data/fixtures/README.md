# Test fixtures

These small synthetic CSVs mimic the WID bulk-download row format
(`country;variable;percentile;year;value`) for three countries
(France, Germany, United States) over 2018-2020. They are **not** real
WID data -- numerical values are plausible but illustrative and
**MUST NOT** be cited.

The fixtures exist for two reasons:

1. The end-to-end pipeline test (`tests/test_pipeline_synthetic.py`)
   uses them to prove ingest -> harmonize -> release -> validation
   works without an outbound network connection.
2. They serve as a worked example of the upstream row format for
   contributors. Real fixtures should be downloaded from
   <https://wid.world/bulk_download/> and placed under
   `data/raw/wid/`.
