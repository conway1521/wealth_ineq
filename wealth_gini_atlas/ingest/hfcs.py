"""HFCS / Eurostat household wealth ingest (v0.2 placeholder).

The ECB's Household Finance and Consumption Survey publishes
distributional indicators (Gini, top decile share, mean and median net
wealth) by country and survey wave. The current release waves are
roughly 2010, 2014, 2017, 2021.

This stub documents the expected data shape and the harmonization
contract; implementation will land with v0.2.

Source landing pages
--------------------

* HFCS results portal:
    https://www.ecb.europa.eu/stats/ecb_surveys/hfcs/html/index.en.html
* Eurostat household financial assets / liabilities:
    https://ec.europa.eu/eurostat/web/sector-accounts/data/main-tables

Harmonization notes
-------------------

* ``unit_of_analysis = household`` (HFCS native unit).
* ``equivalence_scale = none`` for the headline; OECD-modified variant
  can be added later as a supplementary release variable.
* ``comparability_tier = "A"`` for direct HFCS publications: the survey
  is explicitly harmonized across euro-area countries.
* Negative-wealth handling: HFCS reports include households with
  negative net wealth; apply the project's zero-out rule to the
  headline Gini and store the negative-wealth share separately
  (HFCS publishes this directly in some waves).
"""

from __future__ import annotations


def fetch(*_args, **_kwargs):
    raise NotImplementedError("HFCS ingest lands in v0.2 -- see docs/methods.md")


def parse(*_args, **_kwargs):
    raise NotImplementedError("HFCS parse lands in v0.2")
