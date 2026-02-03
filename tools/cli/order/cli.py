"""Orders CLI entry point.

This is accessed via `python -m tools.cli order ...` or from the top-level
interactive menu in `python -m tools.cli`.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from .compare import compare_interactive
from .report import generate_order_compare_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tools.cli order",
        description="Order tooling (compare/manual-vs-cloud)",
    )

    sub = parser.add_subparsers(dest="cmd")

    p_compare = sub.add_parser("compare", help="Compare manual baseline vs cloud")
    p_compare.add_argument(
        "--dir",
        type=Path,
        default=Path("invoices"),
        help="Directory that contains order inputs (default: invoices)",
    )
    p_compare.add_argument(
        "--base",
        default=None,
        help="Base filename without suffix (e.g. 72056547). If omitted: interactive picker.",
    )
    p_compare.add_argument(
        "--max-diffs",
        type=int,
        default=50,
        help="Max diff entries to include per comparison (default: 50)",
    )

    p_compare.add_argument(
        "--fixtures-only",
        action="store_true",
        help="Do not run live extraction; fail if a required fixture is missing.",
    )

    p_compare.add_argument(
        "--refresh-fixtures",
        action="store_true",
        help="Re-run extraction and overwrite existing fixtures (prompts for confirmation unless --yes).",
    )

    p_compare.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Assume yes for overwrite prompts (use with --refresh-fixtures).",
    )

    p_compare.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Write JSON report to this path (default: reports/order/compare_<base>_<ts>.json)",
    )

    p_compare.add_argument(
        "--no-html",
        action="store_true",
        help="Do not generate HTML report (default: generate stable reports/order/compare_<base>.html)",
    )

    p_report = sub.add_parser("report", help="Generate HTML report from compare JSON")
    p_report.add_argument(
        "--in",
        dest="input_json",
        required=True,
        type=Path,
        help="Input compare JSON (reports/order/compare_*.json)",
    )
    p_report.add_argument(
        "--out",
        dest="output_html",
        default=None,
        type=Path,
        help="Write HTML report to this path (default: reports/order/compare_<base>_<ts>.html)",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    cmd = getattr(args, "cmd", None)

    if not cmd:
        # MVP: only compare exists, so treat empty command as compare.
        return compare_interactive(
            root_dir=Path("invoices"),
            base=None,
            max_diffs=50,
            output_path=None,
        )

    if cmd == "compare":
        return compare_interactive(
            root_dir=args.dir,
            base=args.base,
            max_diffs=args.max_diffs,
            output_path=args.out,
            fixtures_only=bool(args.fixtures_only),
            write_html=not bool(args.no_html),
            refresh_fixtures=bool(args.refresh_fixtures),
            assume_yes=bool(args.yes),
        )

    if cmd == "report":
        out = generate_order_compare_report(
            input_json=args.input_json,
            output_html=args.output_html,
        )
        print(f"✅ HTML report: {out}")
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
