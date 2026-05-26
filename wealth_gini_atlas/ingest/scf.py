"""Survey of Consumer Finances (SCF) ingest (v0.3 placeholder).

The Federal Reserve Board publishes triennial SCF microdata
(public-use file) and a chartbook of published distributional
statistics. The chartbook tables (CSV/XLSX) are the v0.3 entry point;
microdata + replicate weights are the v0.4 path for direct Gini
computation.

Source landing pages
--------------------

* SCF home / chartbook:
    https://www.federalreserve.gov/econres/scfindex.htm
* Public-use microdata:
    https://www.federalreserve.gov/econres/scf_2022.htm

Harmonization notes
-------------------

* ``unit_of_analysis = household`` (SCF primary economic unit).
* SCF uses five implicates (multiply imputed); the Gini must be
  computed per implicate and averaged using Rubin's rules. Replicate
  weights are used for standard errors (v0.4).
* ``comparability_tier = "B"`` against HFCS at the country level
  (different sampling, different concept boundaries).
* ``top_tail_flag = "survey_only"`` for raw SCF; flip to
  ``"admin_enhanced"`` for any series imported from Saez-Zucman style
  capitalization work.
"""

from __future__ import annotations


def fetch(*_args, **_kwargs):
    raise NotImplementedError("SCF ingest lands in v0.3 -- see docs/methods.md")


def parse(*_args, **_kwargs):
    raise NotImplementedError("SCF parse lands in v0.3")
