"""
cli.py — HSAE v6.2.0 Command-Line Interface
=============================================
Usage:
    hydrosovereign analyze "Blue Nile (GERD)"
    hydrosovereign analyze --runoff 0.38 --cap 74 --countries 3 --dispute 4
    hydrosovereign list-basins
    hydrosovereign rank-all

Author: Seifeldin M.G. Alkhedir · ORCID: 0000-0003-0821-2991
"""
from __future__ import annotations
import argparse
import json
import sys
import logging


def _setup_logging(verbose: bool):
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(format="%(levelname)s: %(message)s", level=level)


def cmd_analyze(args):
    from .api import analyze_basin
    kwargs = {"include_negotiation": not args.no_ai, "include_legal": not args.no_legal}
    if args.basin:
        kwargs["name"] = args.basin
    else:
        if None in (args.runoff, args.cap, args.countries, args.dispute):
            print("ERROR: Provide --basin name OR all of --runoff --cap --countries --dispute")
            sys.exit(1)
        kwargs.update(runoff_c=args.runoff, cap_bcm=args.cap,
                      n_countries=args.countries, dispute_level=args.dispute)
    result = analyze_basin(**kwargs)
    if args.json:
        # Convert AlertLevel enums to strings for JSON
        print(json.dumps(result, indent=2, default=str))
    else:
        idx = result["indices"]
        meta= result["metadata"]
        print(f"\n{'='*55}")
        print(f"  HSAE Analysis — {meta['name']}")
        print(f"{'='*55}")
        print(f"  ATDI: {idx['atdi']:.1f}%   HIFD: {idx['hifd']:.1f}%")
        print(f"  WQI:  {idx['wqi']:.1f}     CI:   {idx['ci']:.3f}")
        alert = result["alerts"]
        print(f"  Alert:  ATDI={alert['atdi_alert']}  HIFD={alert['hifd_alert']}")
        if result.get("ai"):
            ai = result["ai"]
            print(f"  Neg AI: P(success)={ai['p_success']:.0%}  Strategy={ai['strategy']}")
        if result.get("legal"):
            lg = result["legal"]
            print(f"  Articles: {', '.join(lg['articles'])}")
            print(f"  Rec: {lg['recommendation'][:60]}...")
        print(f"{'='*55}\n")


def cmd_list_basins(args):
    from .basins import BasinRegistry
    reg = BasinRegistry()
    print(f"\nHydroSovereign — {len(reg)} Transboundary Basins\n")
    continents = {}
    for b in reg.all():
        c = b.get("continent","?")
        continents.setdefault(c, []).append(b["name"])
    for cont, names in sorted(continents.items()):
        print(f"  {cont}:")
        for n in names:
            print(f"    • {n}")
    print()


def cmd_rank_all(args):
    from .api import analyze_all_basins
    print("\nAnalyzing all 26 basins... (may take a moment)")
    results = analyze_all_basins(include_ai=False)
    print(f"\n{'Basin':<35} {'ATDI':>7} {'HIFD':>7} {'CI':>7} {'Alert'}")
    print("-"*65)
    for r in results:
        idx  = r["indices"]
        meta = r["metadata"]
        print(f"  {meta['name']:<33} {idx['atdi']:>6.1f}% {idx['hifd']:>6.1f}% "
              f"{idx['ci']:>6.3f}  {r['alerts']['overall']}")
    print()


def main():
    """hydrosovereign CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="hydrosovereign",
        description="HydroSovereign AI Engine v6.2.0 — Transboundary Water Analysis",
    )
    parser.add_argument("-v","--verbose", action="store_true", help="Verbose logging")
    sub = parser.add_subparsers(dest="command")

    # analyze
    p_ana = sub.add_parser("analyze", help="Analyze a basin")
    p_ana.add_argument("basin", nargs="?", help="Basin name from registry")
    p_ana.add_argument("--runoff",   type=float, help="Runoff coefficient (0-1)")
    p_ana.add_argument("--cap",      type=float, help="Storage capacity (BCM)")
    p_ana.add_argument("--countries",type=int,   help="Number of riparian states")
    p_ana.add_argument("--dispute",  type=int,   help="Dispute level 0-4")
    p_ana.add_argument("--json",     action="store_true", help="Output as JSON")
    p_ana.add_argument("--no-ai",    action="store_true", help="Skip Negotiation AI")
    p_ana.add_argument("--no-legal", action="store_true", help="Skip legal assessment")

    # list-basins
    sub.add_parser("list-basins", help="List all 26 registered basins")

    # rank-all
    sub.add_parser("rank-all", help="Rank all 26 basins by conflict index")

    args = parser.parse_args()
    _setup_logging(args.verbose)

    if   args.command == "analyze":      cmd_analyze(args)
    elif args.command == "list-basins":  cmd_list_basins(args)
    elif args.command == "rank-all":     cmd_rank_all(args)
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
