"""Command-line entry point: `wga <command>`."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from . import __version__
from .compute.pipeline import build_release
from .ingest import hfcs as hfcs_ingest
from .ingest import wid as wid_ingest
from .release.build import write as write_release

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)-7s  %(name)s  %(message)s",
                    datefmt="%H:%M:%S")
log = logging.getLogger("wga")


def cmd_fetch(args: argparse.Namespace) -> int:
    if args.source == "wid":
        countries = args.countries.split(",") if args.countries else None
        path = wid_ingest.fetch(countries=countries)
        log.info("WID raw data ready at %s", path)
        return 0
    if args.source == "hfcs":
        try:
            path = hfcs_ingest.fetch()
        except FileNotFoundError as exc:
            # The exception's message is the user-facing instruction.
            print(str(exc))
            return 1
        log.info("HFCS source ready at %s", path)
        return 0
    log.error("Unknown source: %s", args.source)
    return 2


def cmd_build(args: argparse.Namespace) -> int:
    df = build_release(raw_dir=Path(args.raw_dir) if args.raw_dir else None)
    out_dir = Path(args.out_dir)
    manifest = write_release(df, out_dir, version=args.version)
    log.info("Wrote release v%s: %d rows, %d countries -> %s",
             manifest["version"], manifest["n_rows"], manifest["n_countries"], out_dir)
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    import pandas as pd
    from .schema import validate
    df = pd.read_parquet(args.path) if str(args.path).endswith(".parquet") \
        else pd.read_csv(args.path)
    issues = validate(df, strict=False)
    if issues:
        for i in issues:
            print(f"ISSUE: {i}")
        return 1
    print("OK: release file conforms to schema")
    return 0


def cmd_coverage(args: argparse.Namespace) -> int:
    """Print a (geo x source) presence matrix for a release file.

    Useful diagnostic once multiple sources are ingested -- shows which
    country-source cells are filled and where the gaps are.
    """
    import pandas as pd
    df = pd.read_parquet(args.path) if str(args.path).endswith(".parquet") \
        else pd.read_csv(args.path)

    if df.empty:
        print("empty release file")
        return 0

    presence = (
        df.groupby(["geo_id", "source_dataset"])
          .size()
          .unstack(fill_value=0)
    )
    print(presence.to_string())
    print()
    print(f"countries  : {df['geo_id'].nunique()}")
    print(f"sources    : {sorted(df['source_dataset'].unique().tolist())}")
    print(f"year_range : {int(df['year'].min())}..{int(df['year'].max())}")
    print(f"rows       : {len(df)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="wga", description="Wealth Gini Atlas CLI")
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="cmd", required=True)

    pf = sub.add_parser("fetch", help="Download raw upstream data")
    pf.add_argument("source", choices=["wid", "hfcs"], help="Source to fetch")
    pf.add_argument("--countries", help="Comma-separated ISO-2 codes (default: all, WID only)")
    pf.set_defaults(func=cmd_fetch)

    pb = sub.add_parser("build", help="Build the release tables")
    pb.add_argument("--raw-dir", help="Override raw data directory")
    pb.add_argument("--out-dir", default="data/release",
                    help="Where to write CSV/Parquet/manifest")
    pb.add_argument("--version", default=None,
                    help="Override version string in output filenames")
    pb.set_defaults(func=cmd_build)

    pv = sub.add_parser("validate", help="Schema-validate a release file")
    pv.add_argument("path", help="Path to CSV or Parquet file")
    pv.set_defaults(func=cmd_validate)

    pc = sub.add_parser("coverage",
                        help="Print a country x source coverage matrix")
    pc.add_argument("path", help="Path to CSV or Parquet release file")
    pc.set_defaults(func=cmd_coverage)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":   # pragma: no cover
    sys.exit(main())
