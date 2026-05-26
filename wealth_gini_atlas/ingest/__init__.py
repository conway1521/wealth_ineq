"""Source-specific ingest modules.

Each module exposes a `fetch()` function that writes raw upstream files
into `data/raw/<source>/` and a `parse()` function that returns a tidy
intermediate DataFrame for the harmonizer.
"""
