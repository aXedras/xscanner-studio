"""Strategy comparison and evaluation core logic."""

import os
import signal
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any

from xscanner.strategy.base import ExtractionResult, ExtractionStrategy

from .synonyms import (
    get_producer_candidates,
    normalize_fineness_value,
    normalize_producer,
    normalize_unit,
    weight_to_grams,
)

# Global flag for graceful shutdown
_shutdown_requested = False


def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully."""
    global _shutdown_requested
    _shutdown_requested = True
    print("\n\n⚠️  Shutdown requested (Ctrl+C). Waiting for current tasks to complete...")
    print("    Press Ctrl+C again to force exit.\n")
    # Re-register to allow force exit on second Ctrl+C
    signal.signal(signal.SIGINT, signal.SIG_DFL)


# Register signal handler
signal.signal(signal.SIGINT, signal_handler)


def get_image_parallel_workers() -> int:
    """Get number of parallel image workers from env vars.

    Set to 0 (default) to disable image-level parallelization.
    Recommended: Set to CPU_count / STRATEGY_WORKERS for optimal throughput.
    """
    try:
        raw = os.getenv("STRATEGY_IMAGE_WORKERS")
        if raw is None:
            # Legacy env var name (deprecated)
            raw = os.getenv("OCR_IMAGE_WORKERS", "0")
        return max(0, int(raw))
    except ValueError:
        return 0


class StrategyComparator:
    """Compares multiple extraction strategies on the same images."""

    def __init__(
        self,
        strategies: list[ExtractionStrategy],
        max_workers: int | None = None,
        image_workers: int | None = None,
    ):
        """Initialize comparator with strategies.

        Args:
            strategies: List of strategies to test
            max_workers: Number of parallel workers per image (strategy-level)
            image_workers: Number of images to process in parallel (0 = sequential)
        """
        self.strategies = strategies
        self.results: list[dict[str, Any]] = []
        self.max_workers = max(1, max_workers or 1)
        self.image_workers = (
            image_workers if image_workers is not None else get_image_parallel_workers()
        )

    def test_image(self, image_path: Path) -> dict[str, ExtractionResult]:
        """Test all strategies on a single image.

        Args:
            image_path: Path to image file

        Returns:
            Dictionary mapping strategy name to result
        """
        worker_count = self._effective_worker_count()

        if worker_count > 1:
            return self._run_strategies_parallel(image_path, worker_count)

        return self._run_strategies_sequential(image_path)

    def test_multiple_images(self, image_cases: list[Any]) -> list[dict[str, Any]]:
        """Test all strategies on multiple images.

        Args:
            image_cases: List of image paths or dictionaries with metadata

        Returns:
            List of test results
        """
        if self.image_workers > 1 and len(image_cases) > 1:
            return self._test_multiple_images_parallel(image_cases)
        return self._test_multiple_images_sequential(image_cases)

    def save_results(self, output_path: Path):
        """Save results to JSON file."""
        import json

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Results saved to: {output_path}")

    def get_best_strategy(self) -> str:
        """Determine best performing strategy based on confidence and completeness."""
        if not self.results:
            return "No results available"

        strategy_scores: dict[str, list[float]] = {}

        for test in self.results:
            for strategy_name, result in test["results"].items():
                if strategy_name not in strategy_scores:
                    strategy_scores[strategy_name] = []

                # Score based on confidence and number of extracted fields
                if not result["error"]:
                    confidence = result["confidence"] or 0
                    completeness = sum(1 for v in result["structured_data"].values() if v) / 7
                    score = (confidence + completeness) / 2
                    strategy_scores[strategy_name].append(score)

        # Calculate average scores
        avg_scores = {
            name: sum(scores) / len(scores) for name, scores in strategy_scores.items() if scores
        }

        if not avg_scores:
            return "No successful extractions"

        best = max(avg_scores.items(), key=lambda x: x[1])
        return f"{best[0]} (avg score: {best[1]:.2%})"

    def print_comparison(self):
        """Print formatted comparison of results."""
        if not self.results:
            print("No results to compare")
            return

        print(f"\n\n{'=' * 80}")
        print("COMPARISON SUMMARY")
        print(f"{'=' * 80}\n")

        for test in self.results:
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
                            field
                            for field, ok in comparison.get("field_matches", {}).items()
                            if not ok
                        ]
                        if missing:
                            print(f"    Missing fields: {', '.join(missing)}")

    # Private methods

    def _run_strategies_sequential(self, image_path: Path) -> dict[str, ExtractionResult]:
        """Execute strategies one by one."""
        results: dict[str, ExtractionResult] = {}
        print(f"\n{'=' * 80}")
        print(f"Testing: {image_path.name}")
        print(f"{'=' * 80}")

        for strategy in self.strategies:
            print(f"\n  Running {strategy.name}...", end=" ")
            result = self._run_strategy_safe(strategy, image_path)
            results[strategy.name] = result

            if result.error:
                print(f"❌ Error: {result.error}")
            else:
                print(f"✓ Done ({result.processing_time:.2f}s)")

        return results

    def _run_strategies_parallel(
        self, image_path: Path, worker_count: int
    ) -> dict[str, ExtractionResult]:
        """Execute strategies in parallel using ThreadPoolExecutor."""
        print(f"\n{'=' * 80}")
        print(f"Testing: {image_path.name}")
        print(f"{'=' * 80}")
        print(f"\n  Executing with {worker_count} parallel workers...")

        completion: dict[str, ExtractionResult] = {}
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            future_map = {
                executor.submit(self._run_strategy_safe, strategy, image_path): strategy
                for strategy in self.strategies
            }
            for future in as_completed(future_map):
                strategy = future_map[future]
                print(f"\n  Running {strategy.name} (parallel)...", end=" ")
                try:
                    result = future.result()
                except Exception as exc:
                    result = ExtractionResult(
                        raw_text="",
                        structured_data={},
                        confidence=None,
                        processing_time=None,
                        strategy_name=strategy.name,
                        error=str(exc),
                    )
                completion[strategy.name] = result
                if result.error:
                    print(f"❌ Error: {result.error}")
                else:
                    proc_time = result.processing_time or 0.0
                    print(f"✓ Done ({proc_time:.2f}s)")

        # Preserve declared strategy order for downstream consumers
        ordered_results: dict[str, ExtractionResult] = {}
        for strategy in self.strategies:
            strategy_result: ExtractionResult | None = completion.get(strategy.name)
            if strategy_result is not None:
                ordered_results[strategy.name] = strategy_result
        return ordered_results

    def _test_multiple_images_sequential(self, image_cases: list[Any]) -> list[dict[str, Any]]:
        """Process images sequentially (original behavior)."""
        all_results = []

        for case in image_cases:
            result = self._process_single_image_case(case)
            all_results.append(result)

        self.results = all_results
        return all_results

    def _test_multiple_images_parallel(self, image_cases: list[Any]) -> list[dict[str, Any]]:
        """Process multiple images in parallel using ThreadPoolExecutor."""
        global _shutdown_requested
        _shutdown_requested = False  # Reset on new run

        worker_count = min(self.image_workers, len(image_cases))
        print(f"\n{'#' * 80}")
        print(f"# Processing {len(image_cases)} images with {worker_count} parallel image workers")
        print(f"# (Each image uses up to {self.max_workers} strategy workers)")
        print("# Press Ctrl+C to stop gracefully")
        print(f"{'#' * 80}\n")

        results_map: dict[int, dict[str, Any]] = {}

        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            future_to_index = {
                executor.submit(self._process_single_image_case, case): idx
                for idx, case in enumerate(image_cases)
            }

            for future in as_completed(future_to_index):
                if _shutdown_requested:
                    print("\n⚠️  Cancelling remaining tasks...")
                    executor.shutdown(wait=False, cancel_futures=True)
                    break

                idx = future_to_index[future]
                try:
                    result = future.result()
                    results_map[idx] = result
                    print(
                        f"  ✓ Completed image {idx + 1}/{len(image_cases)}: {Path(result['image']).name}"
                    )
                except Exception as exc:
                    image_path, _ = self._extract_case(image_cases[idx])
                    results_map[idx] = {
                        "image": str(image_path),
                        "timestamp": datetime.now().isoformat(),
                        "expected": None,
                        "results": {},
                        "error": str(exc),
                    }
                    print(f"  ✗ Failed image {idx + 1}/{len(image_cases)}: {exc}")

        # Preserve original order - handle missing results from cancelled tasks
        all_results = []
        for i in range(len(image_cases)):
            if i in results_map:
                all_results.append(results_map[i])
            else:
                # Task was cancelled or never completed
                image_path, expected = self._extract_case(image_cases[i])
                all_results.append(
                    {
                        "image": str(image_path),
                        "timestamp": datetime.now().isoformat(),
                        "expected": expected,
                        "results": {},
                        "error": "Task cancelled due to shutdown",
                    }
                )
        self.results = all_results
        return all_results

    def _process_single_image_case(self, case: Any) -> dict[str, Any]:
        """Process a single image case and return the result dict."""
        image_path, expected = self._extract_case(case)
        strategy_results = self.test_image(image_path)

        return {
            "image": str(image_path),
            "timestamp": datetime.now().isoformat(),
            "expected": expected,
            "results": {
                name: {
                    "raw_text": result.raw_text[:200] + "..."
                    if len(result.raw_text) > 200
                    else result.raw_text,
                    "structured_data": result.structured_data,
                    "confidence": result.confidence,
                    "processing_time": result.processing_time,
                    "error": result.error,
                    "comparison": self._evaluate_result(expected, result.structured_data),
                }
                for name, result in strategy_results.items()
            },
        }

    def _extract_case(self, case: Any) -> tuple[Path, dict[str, Any] | None]:
        """Extract image path and expected metadata from test case."""
        if isinstance(case, dict):
            return Path(case["image"]), case.get("expected")
        return Path(case), None

    def _effective_worker_count(self) -> int:
        """Calculate effective number of workers based on available strategies."""
        if not self.strategies:
            return 0
        return min(self.max_workers, len(self.strategies))

    def _run_strategy_safe(
        self, strategy: ExtractionStrategy, image_path: Path
    ) -> ExtractionResult:
        """Execute strategy with error handling."""
        try:
            return strategy.extract(image_path)
        except Exception as exc:
            return ExtractionResult(
                raw_text="",
                structured_data={},
                confidence=None,
                processing_time=None,
                strategy_name=strategy.name,
                error=str(exc),
            )

    def _evaluate_result(
        self, expected: dict[str, Any] | None, extracted: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Compare extracted data with expected values."""
        if not expected or "fields" not in expected:
            return None

        expected_fields = expected["fields"]
        field_matches: dict[str, bool] = {}
        matched_count = 0

        for field, expected_value in expected_fields.items():
            actual = extracted.get(field)
            if self._fields_match(field, expected_value, actual):
                field_matches[field] = True
                matched_count += 1
            else:
                field_matches[field] = False

        total_fields = len(expected_fields)
        return {
            "matched_fields": matched_count,
            "total_expected_fields": total_fields,
            "field_matches": field_matches,
            "pass": matched_count == total_fields,
        }

    def _fields_match(self, field_name: str, expected: Any, actual: Any) -> bool:
        """Check if field values match with normalization."""
        if expected is None:
            return actual is None

        if actual is None:
            return False

        field_lower = field_name.lower()

        # Producer comparison with synonyms
        if "producer" in field_lower:
            expected_norm = normalize_producer(expected)
            actual_candidates = get_producer_candidates(actual)
            return expected_norm in actual_candidates if expected_norm else False

        # Weight comparison (convert to grams)
        if "weight" in field_lower and "unit" not in field_lower:
            expected_weight = weight_to_grams(expected, None)
            actual_weight = weight_to_grams(actual, None)
            if expected_weight and actual_weight:
                return abs(expected_weight - actual_weight) < 0.01
            return False

        # Unit comparison
        if "unit" in field_lower:
            expected_unit = normalize_unit(expected)
            actual_unit = normalize_unit(actual)
            return expected_unit == actual_unit

        # Fineness comparison
        if "fineness" in field_lower or "purity" in field_lower:
            expected_fin = normalize_fineness_value(expected)
            actual_fin = normalize_fineness_value(actual)
            if expected_fin and actual_fin:
                return abs(expected_fin - actual_fin) < 0.001
            return False

        # Default: case-insensitive string comparison
        return str(expected).strip().lower() == str(actual).strip().lower()
