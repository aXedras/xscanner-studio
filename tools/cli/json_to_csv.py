#!/usr/bin/env python3
"""Convert existing JSON benchmark results to CSV format."""

import csv
import json
import sys
from pathlib import Path


def json_to_csv(json_path: Path, csv_path: Path | None = None):
    """Convert JSON benchmark results to CSV.

    Args:
        json_path: Path to JSON results file
        csv_path: Output CSV path (default: same name with .csv extension)
    """
    if csv_path is None:
        csv_path = json_path.with_suffix(".csv")

    with open(json_path, encoding="utf-8") as f:
        results = json.load(f)

    if not results:
        print("No results in JSON file")
        return

    # Collect all strategy names
    strategy_names = set()
    for test in results:
        strategy_names.update(test.get("results", {}).keys())
    strategy_names = sorted(strategy_names)

    # Define field order
    fields = ["SerialNumber", "Metal", "Weight", "WeightUnit", "Fineness", "Producer"]

    # Build header row
    header = ["Image"]
    for field in fields:
        header.append(f"Expected_{field}")
    for strategy in strategy_names:
        for field in fields:
            header.append(f"{strategy}_{field}")
        header.append(f"{strategy}_Match")
        header.append(f"{strategy}_Time")

    rows = [header]

    for test in results:
        row = [test.get("image", "")]

        # Expected values
        expected = test.get("expected", {}).get("fields", {})
        for field in fields:
            row.append(expected.get(field, ""))

        # Per-strategy values
        for strategy in strategy_names:
            result = test.get("results", {}).get(strategy, {})
            structured = result.get("structured_data", {})
            comparison = result.get("comparison", {})

            for field in fields:
                value = structured.get(field, "")
                field_matches = comparison.get("field_matches", {})
                match = field_matches.get(field)
                if match is True:
                    value = f"✓ {value}"
                elif match is False:
                    value = f"✗ {value}"
                row.append(value)

            matched = comparison.get("matched_fields", "")
            total = comparison.get("total_expected_fields", "")
            row.append(f"{matched}/{total}" if matched != "" else "")

            time_val = result.get("processing_time")
            row.append(f"{time_val:.1f}s" if time_val else "")

        rows.append(row)

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    print(f"✓ Converted {len(results)} results to: {csv_path}")
    print(f"  Strategies: {', '.join(strategy_names)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python json_to_csv.py <json_file> [csv_file]")
        print("\nExamples:")
        print("  python json_to_csv.py reports/strategy_benchmark_results.json")
        print("  python json_to_csv.py results.json output.csv")
        sys.exit(1)

    json_file = Path(sys.argv[1])
    csv_file = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    if not json_file.exists():
        print(f"Error: File not found: {json_file}")
        sys.exit(1)

    json_to_csv(json_file, csv_file)
