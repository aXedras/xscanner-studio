"""Result formatting and presentation for strategy comparison."""

from pathlib import Path
from typing import Any


def calculate_strategy_scores(results: list[dict[str, Any]]) -> dict[str, float]:
    """Calculate average scores for all strategies.

    Score calculation:
    - If comparison data available: score = (confidence + accuracy) / 2
    - Otherwise: score = confidence

    Where:
    - confidence = model_confidence × completeness (from strategy)
    - accuracy = matched_fields / total_expected_fields (from comparison)

    Args:
        results: List of test results

    Returns:
        Dictionary mapping strategy names to average scores
    """
    strategy_scores: dict[str, list[float]] = {}

    for test in results:
        for strategy_name, result in test["results"].items():
            if strategy_name not in strategy_scores:
                strategy_scores[strategy_name] = []

            if not result["error"]:
                confidence = result["confidence"] or 0

                # Use accuracy from comparison if available
                comparison = result.get("comparison")
                if comparison and comparison.get("total_expected_fields"):
                    matched = comparison.get("matched_fields", 0)
                    total = comparison.get("total_expected_fields", 1)
                    accuracy = matched / total
                    score = (confidence + accuracy) / 2
                else:
                    # No comparison data, use confidence only
                    score = confidence

                strategy_scores[strategy_name].append(score)

    # Calculate average scores
    return {name: sum(scores) / len(scores) for name, scores in strategy_scores.items() if scores}


def get_best_strategy(results: list[dict[str, Any]]) -> str:
    """Determine best performing strategy based on confidence and accuracy.

    Args:
        results: List of test results

    Returns:
        String describing the best strategy
    """
    if not results:
        return "No results available"

    avg_scores = calculate_strategy_scores(results)

    if not avg_scores:
        return "No successful extractions"

    best = max(avg_scores.items(), key=lambda x: x[1])
    return f"{best[0]} (avg score: {best[1]:.2%})"


def print_comparison(results: list[dict[str, Any]]):
    """Print formatted comparison of results.

    Args:
        results: List of test results to display
    """
    if not results:
        print("No results to compare")
        return

    print(f"\n\n{'=' * 80}")
    print("COMPARISON SUMMARY")
    print(f"{'=' * 80}\n")

    for test in results:
        expected = test.get("expected")
        print(f"\nImage: {Path(test['image']).name}")
        print(f"{'-' * 80}")
        if expected and expected.get("fields"):
            fields = expected["fields"]
            print("  Expected metadata:")
            for key, value in fields.items():
                print(f"    - {key}: {value}")

        for strategy_name, result in test["results"].items():
            print(f"\n  Strategy: {strategy_name}")
            print(
                f"  Confidence: {result['confidence']:.2%}"
                if result["confidence"]
                else "  Confidence: N/A"
            )
            print(
                f"  Time: {result['processing_time']:.2f}s"
                if result["processing_time"]
                else "  Time: N/A"
            )

            if result["error"]:
                print(f"  ❌ Error: {result['error']}")
            else:
                print("  Extracted Data:")
                for key, value in result["structured_data"].items():
                    if value:
                        print(f"    - {key}: {value}")
                comparison = result.get("comparison")
                if comparison and comparison.get("total_expected_fields"):
                    match_count = comparison.get("matched_fields", 0)
                    total_fields = comparison.get("total_expected_fields", 0)
                    status = "✓" if comparison.get("pass") else "✗"
                    print(f"  Comparison: {status} {match_count}/{total_fields} fields matched")
                    missing = [
                        field for field, ok in comparison.get("field_matches", {}).items() if not ok
                    ]
                    if missing:
                        print(f"    Missing fields: {', '.join(missing)}")
