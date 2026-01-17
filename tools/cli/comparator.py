"""Strategy comparison and evaluation core logic."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any

from xscanner.strategy.base import ExtractionResult, ExtractionStrategy

from .execution_manager import (
    get_image_parallel_workers,
    is_shutdown_requested,
    reset_shutdown_flag,
    run_strategies_parallel,
    run_strategies_sequential,
)
from .result_formatter import get_best_strategy, print_comparison
from .validator import parse_filename_ground_truth, validate_extraction


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
            return run_strategies_parallel(self.strategies, image_path, worker_count)

        return run_strategies_sequential(self.strategies, image_path)

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
        return get_best_strategy(self.results)

    def print_comparison(self):
        """Print formatted comparison of results."""
        print_comparison(self.results)

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
        reset_shutdown_flag()  # Reset on new run

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
                if is_shutdown_requested():
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

        # Try to get ground truth from filename if not explicitly provided
        if expected is None:
            ground_truth = parse_filename_ground_truth(image_path)
            if ground_truth:
                expected = {"fields": ground_truth}

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
                    "comparison": self._evaluate_result_with_validator(
                        expected, result.structured_data
                    ),
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

    def _evaluate_result_with_validator(
        self, expected: dict[str, Any] | None, extracted: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Compare extracted data with expected values using centralized validator."""
        if not expected or "fields" not in expected:
            return None

        ground_truth = expected["fields"]

        # Use centralized validator
        successes, errors = validate_extraction(extracted, ground_truth)

        # Build field matches dict
        field_matches: dict[str, bool] = {}
        total_fields = len(ground_truth) - 1  # Exclude WeightUnit from count

        # All fields from ground truth (excluding WeightUnit)
        for field in ["Metal", "Weight", "Fineness", "Producer", "SerialNumber"]:
            if field in ground_truth:
                # Check if this field has an error
                has_error = any(field in error for error in errors)
                field_matches[field] = not has_error

        matched_count = sum(1 for match in field_matches.values() if match)

        return {
            "matched_fields": matched_count,
            "total_expected_fields": total_fields,
            "field_matches": field_matches,
            "pass": len(errors) == 0,
            "errors": errors,  # Include actual error messages
        }
