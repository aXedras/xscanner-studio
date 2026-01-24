"""HTML report generator for strategy benchmark results."""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .renderers import (
    render_aggregate_table,
    render_executive_summary,
    render_failed_tests_section,
    render_hybrid_analysis,
    render_metal_accuracy_section,
    render_strategy_metal_matrix,
    render_summary_chart,
    render_table_rows,
)
from .report_models import (
    aggregate_by_metal,
    aggregate_by_strategy,
    aggregate_strategy_by_metal,
    calculate_hybrid_potential,
    load_results,
)
from .result_formatter import calculate_strategy_scores
from .template import HTML_TEMPLATE, INDEX_TEMPLATE

DATA_PATH = Path("reports/strategy_benchmark_results.json")
OUTPUT_PATH = Path("reports/strategy_benchmark_report.html")
HISTORY_DIR = Path("reports/history")


def generate_reports(
    *,
    input_path: Path = DATA_PATH,
    output_path: Path = OUTPUT_PATH,
    regenerate: bool = False,
) -> None:
    """Generate current HTML report and update history reports + index.

    This is used by both the report CLI entry point and the benchmark runner.
    """
    if not input_path.exists():
        print(f"❌ Error: Input file not found: {input_path}")
        print("\n💡 Run benchmark first: make cli-benchmark")
        return

    payload = load_results(input_path)
    html = build_html(payload, output_path=output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(f"✅ Current report written to {output_path}")

    if not HISTORY_DIR.exists():
        print("\n💡 No history directory yet (will be created after first benchmark)")
        return

    json_files = sorted(HISTORY_DIR.glob("strategy_benchmark_results_*.json"))
    if not json_files:
        print("\n💡 No history files found yet")
        return

    print(f"\n📁 Processing {len(json_files)} history file(s)...")

    generated_count = 0
    skipped_count = 0
    for json_file in json_files:
        result = generate_history_report(json_file, force_regenerate=regenerate)
        if result:
            print(f"  ✅ Generated: {result.name}")
            generated_count += 1
        else:
            skipped_count += 1

    if skipped_count > 0:
        print(f"  ⏭️  Skipped {skipped_count} existing report(s) (use --regenerate to force)")

    print(f"\n📊 Generated {generated_count} history report(s)")
    generate_index_page(HISTORY_DIR)


def build_html(payload: list[dict[str, Any]], output_path: Path = OUTPUT_PATH) -> str:
    """Build complete HTML report from benchmark results.

    Args:
        payload: List of benchmark test results
        output_path: Path where HTML will be saved (kept for compatibility, not used for image paths)

    Returns:
        Complete HTML document as string
    """
    aggregates = aggregate_by_strategy(payload)
    metal_aggregates = aggregate_by_metal(payload)
    strategy_metal_stats = aggregate_strategy_by_metal(payload)
    hybrid_potentials = calculate_hybrid_potential(payload, aggregates)

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    image_count = len(payload)
    strategy_count = len(aggregates)
    expected_images = sum(
        1
        for entry in payload
        if isinstance(entry.get("expected"), dict) and (entry.get("expected") or {}).get("fields")
    )
    summary_text = (
        f"{strategy_count} strategies were benchmarked across {image_count} image"
        f"{'s' if image_count != 1 else ''}."
    )
    if expected_images:
        summary_text += (
            f" Ground-truth metadata is available for {expected_images} image"
            f"{'s' if expected_images != 1 else ''}."
        )

    # Render all sections
    exec_summary = render_executive_summary(aggregates)
    metal_accuracy_section = render_metal_accuracy_section(metal_aggregates, strategy_metal_stats)
    strategy_metal_matrix = render_strategy_metal_matrix(strategy_metal_stats)
    hybrid_analysis = render_hybrid_analysis(hybrid_potentials)

    return HTML_TEMPLATE.format(
        created_at=created_at,
        summary_text=summary_text,
        exec_summary=exec_summary,
        metal_accuracy_section=metal_accuracy_section,
        strategy_metal_matrix=strategy_metal_matrix,
        hybrid_analysis=hybrid_analysis,
        summary_chart=render_summary_chart(aggregates),
        failed_tests_section=render_failed_tests_section(payload),
        aggregate_rows=render_aggregate_table(aggregates),
        image_sections=render_table_rows(payload),
    )


def generate_history_report(json_file: Path, force_regenerate: bool = False) -> Path | None:
    """Generate HTML report for a specific history JSON file.

    Args:
        json_file: Path to the history JSON file
        force_regenerate: If True, regenerate even if HTML exists

    Returns:
        Path to generated HTML file, or None if skipped
    """
    # Extract timestamp from filename: strategy_benchmark_results_20260117_090433.json
    stem = json_file.stem  # strategy_benchmark_results_20260117_090433
    timestamp = stem.split("_")[-2] + "_" + stem.split("_")[-1]  # 20260117_090433

    html_file = json_file.parent / f"report_{timestamp}.html"

    # Skip if HTML exists and not forcing regeneration
    if html_file.exists() and not force_regenerate:
        return None

    # Generate report
    payload = load_results(json_file)
    html = build_html(payload, output_path=html_file)
    html_file.write_text(html, encoding="utf-8")

    return html_file


def generate_index_page(history_dir: Path) -> None:
    """Generate index.html with overview of all history reports.

    Args:
        history_dir: Path to history directory
    """
    # Find all JSON files in history
    json_files = sorted(history_dir.glob("strategy_benchmark_results_*.json"), reverse=True)

    if not json_files:
        print("⚠️  No history files found")
        return

    # Build index data
    rows = []
    for json_file in json_files:
        # Extract timestamp from filename
        stem = json_file.stem
        timestamp = stem.split("_")[-2] + "_" + stem.split("_")[-1]

        # Parse timestamp for display
        dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
        display_date = dt.strftime("%Y-%m-%d %H:%M:%S")

        # Load JSON to get summary stats
        try:
            with open(json_file, encoding="utf-8") as f:
                data = json.load(f)

            image_count = len(data)
            strategies = set()
            for entry in data:
                strategies.update(entry.get("results", {}).keys())
            strategy_count = len(strategies)

            # Calculate best strategy score using shared function
            avg_scores = calculate_strategy_scores(data)

            best_strategy = max(avg_scores.items(), key=lambda x: x[1])[0] if avg_scores else "N/A"
            avg_score = f"{max(avg_scores.values()):.1%}" if avg_scores else "0%"

            # HTML file link
            html_link = f"report_{timestamp}.html"

            rows.append(
                f"""
                <tr>
                    <td>{display_date}</td>
                    <td>{image_count}</td>
                    <td>{strategy_count}</td>
                    <td>{best_strategy}</td>
                    <td>{avg_score}</td>
                    <td><a href="{html_link}" target="_blank">View Report</a></td>
                </tr>
                """
            )
        except Exception as e:
            print(f"⚠️  Error processing {json_file.name}: {e}")
            continue

    # Generate HTML
    table_rows = "\n".join(rows)
    html = INDEX_TEMPLATE.format(
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        total_runs=len(rows),
        table_rows=table_rows,
    )

    # Save index
    index_file = history_dir / "index.html"
    index_file.write_text(html, encoding="utf-8")
    print(f"📋 Index page written to {index_file}")


def main() -> None:
    """Main entry point for report generator CLI."""
    parser = argparse.ArgumentParser(
        description="📊 Generate HTML report from benchmark results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m tools.cli.report                         # Generate current + missing history reports
  python -m tools.cli.report --regenerate            # Regenerate all history reports
  python -m tools.cli.report --input custom.json --output custom.html
  make cli-report
  make cli-report-history
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

    parser.add_argument(
        "--regenerate",
        action="store_true",
        help="Regenerate all history reports (even if HTML exists)",
    )

    args = parser.parse_args()

    generate_reports(input_path=args.input, output_path=args.output, regenerate=args.regenerate)


if __name__ == "__main__":
    main()
