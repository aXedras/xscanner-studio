"""HTML report generator for OCR strategy benchmark results."""

import argparse
from datetime import datetime
from pathlib import Path
from typing import Any

from .renderers import render_aggregate_table, render_summary_chart, render_table_rows
from .report_models import aggregate_by_strategy, load_results
from .template import HTML_TEMPLATE

DATA_PATH = Path("reports/strategy_benchmark_results.json")
OUTPUT_PATH = Path("reports/strategy_benchmark_report.html")


def build_html(payload: list[dict[str, Any]]) -> str:
    """Build complete HTML report from benchmark results.

    Args:
        payload: List of benchmark test results

    Returns:
        Complete HTML document as string
    """
    aggregates = aggregate_by_strategy(payload)
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    image_count = len(payload)
    strategy_count = len(aggregates)
    expected_images = sum(
        1
        for entry in payload
        if isinstance(entry.get("expected"), dict) and (entry.get("expected") or {}).get("fields")
    )
    summary_text = (
        f"{strategy_count} OCR strategies were benchmarked across {image_count} image"
        f"{'s' if image_count != 1 else ''}."
    )
    if expected_images:
        summary_text += (
            f" Ground-truth metadata is available for {expected_images} image"
            f"{'s' if expected_images != 1 else ''}."
        )

    return HTML_TEMPLATE.format(
        created_at=created_at,
        summary_text=summary_text,
        summary_chart=render_summary_chart(aggregates),
        aggregate_rows=render_aggregate_table(aggregates),
        image_sections=render_table_rows(payload),
    )


def main() -> None:
    """Main entry point for report generator CLI."""
    parser = argparse.ArgumentParser(
        description="📊 Generate HTML report from benchmark results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m tools.cli.report
  python -m tools.cli.report --input results.json --output report.html
  make cli-report
        """,
    )

    parser.add_argument(
        "--input", type=Path, default=DATA_PATH, help=f"Input JSON file (default: {DATA_PATH})"
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_PATH,
        help=f"Output HTML file (default: {OUTPUT_PATH})",
    )

    args = parser.parse_args()

    if not args.input.exists():
        print(f"❌ Error: Input file not found: {args.input}")
        print("\n💡 Run benchmark first: make benchmark-run")
        return

    payload = load_results(args.input)
    html = build_html(payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html, encoding="utf-8")
    print(f"✅ Report written to {args.output}")


if __name__ == "__main__":
    main()
