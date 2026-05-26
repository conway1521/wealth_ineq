"""Write release artifacts: CSV, Parquet, manifest JSON."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .. import __version__, METHOD_VERSION


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def write(df: pd.DataFrame, out_dir: Path, version: str | None = None) -> dict:
    """Write CSV + Parquet + manifest. Returns the manifest dict."""
    out_dir.mkdir(parents=True, exist_ok=True)
    version = version or __version__

    csv_path = out_dir / f"wealth_gini_atlas_v{version}.csv"
    pq_path = out_dir / f"wealth_gini_atlas_v{version}.parquet"

    df.to_csv(csv_path, index=False)
    df.to_parquet(pq_path, index=False)

    manifest = {
        "name": "Wealth Gini Atlas",
        "version": version,
        "method_version": METHOD_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "n_rows": int(len(df)),
        "n_countries": int(df["geo_id"].nunique()) if not df.empty else 0,
        "year_min": int(df["year"].min()) if not df.empty else None,
        "year_max": int(df["year"].max()) if not df.empty else None,
        "sources": sorted(df["source_dataset"].dropna().unique().tolist())
                   if not df.empty else [],
        "files": [
            {"path": csv_path.name, "sha256": _sha256(csv_path),
             "bytes": csv_path.stat().st_size, "format": "csv"},
            {"path": pq_path.name, "sha256": _sha256(pq_path),
             "bytes": pq_path.stat().st_size, "format": "parquet"},
        ],
        "license_data": "CC-BY-4.0",
        "license_code": "MIT",
        "headline_negative_wealth_rule": "zero-out (see docs/methods.md)",
    }
    manifest_path = out_dir / f"wealth_gini_atlas_v{version}.manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    return manifest
