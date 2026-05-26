"""Distributional Financial Accounts (DFA) ingest (v0.3 placeholder).

The Federal Reserve Board's DFA splits the Financial Accounts of the
United States by wealth percentile bucket at quarterly frequency.
Series of interest for v0.3:

* Top 1%, next 9%, next 40%, bottom 50% shares of total net worth.
* Aggregate levels of assets / liabilities by percentile.

Source landing pages
--------------------

* DFA home:
    https://www.federalreserve.gov/releases/efa/efa-distributional-financial-accounts.htm
* DFA dataset download (CSV):
    https://www.federalreserve.gov/releases/efa/dataset/dfa.zip

Harmonization notes
-------------------

* ``unit_of_analysis = household`` (DFA scales SCF micro to Financial
  Accounts totals).
* Quarterly source -> we collapse to annual averages for the panel.
* ``comparability_tier = "B"`` for cross-country (DFA blends survey
  and aggregate accounts).
* ``top_tail_flag = "admin_enhanced"`` because DFA totals are anchored
  to Flow-of-Funds aggregates.
* No native Gini in DFA -- we will reconstruct a Lorenz-curve
  approximation from the published percentile-bucket shares and store
  it with a clear ``method_version`` tag and ``observed_vs_modeled =
  "modeled"``.
"""

from __future__ import annotations


def fetch(*_args, **_kwargs):
    raise NotImplementedError("DFA ingest lands in v0.3 -- see docs/methods.md")


def parse(*_args, **_kwargs):
    raise NotImplementedError("DFA parse lands in v0.3")
