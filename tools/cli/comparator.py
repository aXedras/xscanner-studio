"""Strategy comparison and evaluation core logic."""

import os
import re
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

    def test_multiple_images_map_reduce(self, image_cases: list[Any]) -> list[dict[str, Any]]:
        """Test images using map-reduce pattern: strategies run in PARALLEL.

        Best for: Cloud APIs (ChatGPT, Gemini) with no model loading overhead.

        Each strategy processes ALL images in its own thread.
        Results are then reduced (merged) per image.

        Args:
            image_cases: List of image paths or dictionaries with metadata

        Returns:
            List of test results (same format as test_multiple_images)
        """
        if not self.strategies:
            return []

        print(f"\n{'#' * 80}")
        print("# MAP-REDUCE BENCHMARK (strategies in parallel)")
        print(f"# {len(self.strategies)} strategies × {len(image_cases)} images")
        print("# Best for: Cloud APIs (ChatGPT, Gemini)")
        print("# Press Ctrl+C to stop gracefully")
        print(f"{'#' * 80}\n")

        # Prepare image paths for multiprocessing (must be serializable)
        image_data = []
        for case in image_cases:
            image_path, expected = self._extract_case(case)
            image_data.append(
                {
                    "path": str(image_path),
                    "expected": expected,
                }
            )

        # MAP PHASE: Run each strategy in parallel, each processing all images
        strategy_results = self._map_phase(image_data)

        # REDUCE PHASE: Merge results per image
        merged_results = self._reduce_phase(image_data, strategy_results)

        self.results = merged_results
        return merged_results

    def test_multiple_images_ollama_optimized(self, image_cases: list[Any]) -> list[dict[str, Any]]:
        """Test images optimized for Ollama: models SEQUENTIAL, images parallel.

        Best for: Local Ollama models where model switching is expensive (10-30s).

        Process flow:
        1. Load Model A → process all images (in parallel) → unload
        2. Load Model B → process all images (in parallel) → unload
        3. ...

        This minimizes model switching overhead.

        Args:
            image_cases: List of image paths or dictionaries with metadata

        Returns:
            List of test results (same format as test_multiple_images)
        """
        if not self.strategies:
            return []

        print(f"\n{'#' * 80}")
        print("# OLLAMA-OPTIMIZED BENCHMARK (models sequential, images parallel)")
        print(f"# {len(self.strategies)} strategies × {len(image_cases)} images")
        print("# Best for: Local Ollama models (avoids model switching overhead)")
        print("# Press Ctrl+C to stop gracefully")
        print(f"{'#' * 80}\n")

        # Prepare image paths
        image_data = []
        for case in image_cases:
            image_path, expected = self._extract_case(case)
            image_data.append(
                {
                    "path": str(image_path),
                    "expected": expected,
                }
            )

        # MAP PHASE: Run strategies sequentially, images in parallel
        strategy_results = self._map_phase_ollama_optimized(image_data)

        # REDUCE PHASE: Merge results per image
        merged_results = self._reduce_phase(image_data, strategy_results)

        self.results = merged_results
        return merged_results

    def _map_phase(self, image_data: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        """MAP: Each strategy processes all images in its own thread (PARALLEL).

        This is optimal for Cloud APIs (ChatGPT, Gemini) where there's no
        model loading overhead - just network latency.
        """
        global _shutdown_requested
        _shutdown_requested = False

        strategy_results: dict[str, list[dict[str, Any]]] = {}

        # Use ThreadPoolExecutor for strategies (ProcessPool has pickle issues)
        # Each strategy runs sequentially through all images
        with ThreadPoolExecutor(max_workers=len(self.strategies)) as executor:
            future_to_strategy = {
                executor.submit(
                    self._run_strategy_on_all_images,
                    strategy,
                    image_data,
                ): strategy.name
                for strategy in self.strategies
            }

            completed = 0
            total = len(self.strategies)

            for future in as_completed(future_to_strategy):
                if _shutdown_requested:
                    print("\n⚠️  Cancelling remaining strategies...")
                    executor.shutdown(wait=False, cancel_futures=True)
                    break

                strategy_name = future_to_strategy[future]
                completed += 1

                try:
                    results = future.result()
                    strategy_results[strategy_name] = results
                    success_count = sum(1 for r in results if not r.get("error"))
                    print(
                        f"  ✓ [{completed}/{total}] {strategy_name} finished: "
                        f"{success_count}/{len(image_data)} images successful"
                    )
                except Exception as exc:
                    print(f"  ✗ [{completed}/{total}] {strategy_name} failed: {exc}")
                    # Fill with error results
                    strategy_results[strategy_name] = [{"error": str(exc)} for _ in image_data]

        return strategy_results

    def _map_phase_ollama_optimized(
        self, image_data: list[dict[str, Any]]
    ) -> dict[str, list[dict[str, Any]]]:
        """MAP optimized for Ollama: Process models SEQUENTIALLY, images in parallel.

        Ollama can only load one model at a time. Switching models costs 10-30s.
        This mode processes ALL images with one model before switching to the next.

        Within each model, images can be processed in parallel since the same
        model stays loaded and Ollama handles concurrent requests efficiently.
        """
        global _shutdown_requested
        _shutdown_requested = False

        strategy_results: dict[str, list[dict[str, Any]]] = {}
        total = len(self.strategies)

        print("\n  📋 OLLAMA-OPTIMIZED: Processing models SEQUENTIALLY")
        print(f"     Each model processes all {len(image_data)} images before switching\n")

        for idx, strategy in enumerate(self.strategies):
            if _shutdown_requested:
                print("\n⚠️  Shutdown requested, skipping remaining strategies...")
                break

            strategy_name = strategy.name
            print(f"\n  [{idx+1}/{total}] Loading model: {strategy_name}...")

            try:
                # Process all images with this strategy
                # Images can be parallelized since same model stays loaded
                results = self._run_strategy_on_all_images_parallel(
                    strategy, image_data, parallel_images=self.image_workers or 2
                )
                strategy_results[strategy_name] = results
                success_count = sum(1 for r in results if not r.get("error"))
                print(
                    f"  ✓ [{idx+1}/{total}] {strategy_name} finished: "
                    f"{success_count}/{len(image_data)} images successful"
                )
            except Exception as exc:
                print(f"  ✗ [{idx+1}/{total}] {strategy_name} failed: {exc}")
                strategy_results[strategy_name] = [{"error": str(exc)} for _ in image_data]

        return strategy_results

    def _run_strategy_on_all_images(
        self, strategy: ExtractionStrategy, image_data: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Run a single strategy on all images sequentially."""
        results = []
        strategy_name = strategy.name

        print(f"\n  🚀 {strategy_name} starting ({len(image_data)} images)...")

        for idx, img_info in enumerate(image_data):
            image_path = Path(img_info["path"])

            try:
                result = strategy.extract(image_path)
                results.append(
                    {
                        "raw_text": result.raw_text[:200] + "..."
                        if len(result.raw_text) > 200
                        else result.raw_text,
                        "structured_data": result.structured_data,
                        "confidence": result.confidence,
                        "processing_time": result.processing_time,
                        "error": result.error,
                    }
                )

                status = "✓" if not result.error else "⚠"
                time_str = f"{result.processing_time:.1f}s" if result.processing_time else "N/A"
                print(
                    f"    {status} {strategy_name} [{idx+1}/{len(image_data)}] {image_path.name} ({time_str})"
                )

            except Exception as exc:
                results.append(
                    {
                        "raw_text": "",
                        "structured_data": {},
                        "confidence": None,
                        "processing_time": None,
                        "error": str(exc),
                    }
                )
                print(f"    ✗ {strategy_name} [{idx+1}/{len(image_data)}] {image_path.name}: {exc}")

        return results

    def _run_strategy_on_all_images_parallel(
        self,
        strategy: ExtractionStrategy,
        image_data: list[dict[str, Any]],
        parallel_images: int = 2,
    ) -> list[dict[str, Any]]:
        """Run a single strategy on all images with parallel image processing.

        This is optimized for Ollama: the same model stays loaded while we
        send multiple image requests. Ollama can handle concurrent requests
        to the same model efficiently.

        Args:
            strategy: The extraction strategy to use
            image_data: List of image info dicts
            parallel_images: Number of images to process in parallel (default: 2)
        """
        strategy_name = strategy.name
        total_images = len(image_data)

        print(
            f"\n  🚀 {strategy_name} starting ({total_images} images, {parallel_images} parallel)..."
        )

        # Pre-allocate results list to maintain order
        results = [None] * total_images

        def process_single_image(idx: int, img_info: dict) -> tuple[int, dict]:
            """Process a single image and return (index, result)."""
            image_path = Path(img_info["path"])

            try:
                result = strategy.extract(image_path)
                result_dict = {
                    "raw_text": result.raw_text[:200] + "..."
                    if len(result.raw_text) > 200
                    else result.raw_text,
                    "structured_data": result.structured_data,
                    "confidence": result.confidence,
                    "processing_time": result.processing_time,
                    "error": result.error,
                }

                status = "✓" if not result.error else "⚠"
                time_str = f"{result.processing_time:.1f}s" if result.processing_time else "N/A"
                print(
                    f"    {status} {strategy_name} [{idx+1}/{total_images}] {image_path.name} ({time_str})"
                )

                return idx, result_dict

            except Exception as exc:
                print(f"    ✗ {strategy_name} [{idx+1}/{total_images}] {image_path.name}: {exc}")
                return idx, {
                    "raw_text": "",
                    "structured_data": {},
                    "confidence": None,
                    "processing_time": None,
                    "error": str(exc),
                }

        # Use ThreadPoolExecutor for parallel image processing
        with ThreadPoolExecutor(max_workers=parallel_images) as executor:
            futures = {
                executor.submit(process_single_image, idx, img_info): idx
                for idx, img_info in enumerate(image_data)
            }

            for future in as_completed(futures):
                idx, result = future.result()
                results[idx] = result

        return results

    def _reduce_phase(
        self,
        image_data: list[dict[str, Any]],
        strategy_results: dict[str, list[dict[str, Any]]],
    ) -> list[dict[str, Any]]:
        """REDUCE: Merge results per image across all strategies."""
        print(f"\n{'=' * 80}")
        print("REDUCE PHASE: Merging results per image...")
        print(f"{'=' * 80}\n")

        merged = []

        for idx, img_info in enumerate(image_data):
            image_path = img_info["path"]
            expected = img_info.get("expected")

            image_result = {
                "image": image_path,
                "timestamp": datetime.now().isoformat(),
                "expected": expected,
                "results": {},
            }

            # Collect results from each strategy for this image
            for strategy in self.strategies:
                strategy_name = strategy.name
                if strategy_name in strategy_results:
                    strat_result = strategy_results[strategy_name]
                    if idx < len(strat_result):
                        result_data = strat_result[idx]
                        # Add comparison if expected data available
                        result_data["comparison"] = self._evaluate_result(
                            expected, result_data.get("structured_data", {})
                        )
                        image_result["results"][strategy_name] = result_data

            merged.append(image_result)

        return merged

    def save_results(self, output_path: Path):
        """Save results to JSON file."""
        import json

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Results saved to: {output_path}")

    def save_results_csv(self, output_path: Path):
        """Save results to CSV file for easy human review.

        Creates a wide-format CSV with one row per image and columns for:
        - Image path
        - Expected values (from filename)
        - Each strategy's extracted values
        - Match indicators per field per strategy
        """
        import csv

        if not self.results:
            print("No results to save")
            return

        # Collect all strategy names from results
        strategy_names = set()
        for test in self.results:
            strategy_names.update(test.get("results", {}).keys())
        strategy_names = sorted(strategy_names)

        # Define field order
        fields = ["SerialNumber", "Metal", "Weight", "WeightUnit", "Fineness", "Producer"]

        # Build header row
        header = ["Image"]
        # Expected columns
        for field in fields:
            header.append(f"Expected_{field}")
        # Per-strategy columns
        for strategy in strategy_names:
            for field in fields:
                header.append(f"{strategy}_{field}")
            header.append(f"{strategy}_Match")
            header.append(f"{strategy}_Time")

        rows = [header]

        for test in self.results:
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
                    # Add match indicator
                    field_matches = comparison.get("field_matches", {})
                    match = field_matches.get(field)
                    if match is True:
                        value = f"✓ {value}"
                    elif match is False:
                        value = f"✗ {value}"
                    row.append(value)

                # Overall match count
                matched = comparison.get("matched_fields", "")
                total = comparison.get("total_expected_fields", "")
                row.append(f"{matched}/{total}" if matched != "" else "")

                # Processing time
                time_val = result.get("processing_time")
                row.append(f"{time_val:.1f}s" if time_val else "")

            rows.append(row)

        # Write CSV
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(rows)

        print(f"✓ CSV saved to: {output_path}")

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

        # Check if we should do combined weight+unit comparison
        has_weight = "Weight" in expected_fields
        has_unit = "WeightUnit" in expected_fields

        for field, expected_value in expected_fields.items():
            actual = extracted.get(field)

            # Special handling for Weight and WeightUnit - compare combined
            if field == "Weight" and has_unit:
                # Compare weight+unit combined
                exp_unit = expected_fields.get("WeightUnit")
                act_unit = extracted.get("WeightUnit")
                if self._weight_matches_combined(expected_value, exp_unit, actual, act_unit):
                    field_matches[field] = True
                    matched_count += 1
                else:
                    field_matches[field] = False
            elif field == "WeightUnit" and has_weight:
                # Weight+unit already compared above, check if weight matched
                # If weight matched with combined comparison, unit is implicitly correct
                weight_matched = field_matches.get("Weight", False)
                if weight_matched:
                    field_matches[field] = True
                    matched_count += 1
                else:
                    # Fall back to direct unit comparison
                    if self._fields_match(field, expected_value, actual):
                        field_matches[field] = True
                        matched_count += 1
                    else:
                        field_matches[field] = False
            else:
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

        # Metal comparison (normalize AU/AG/PT/PD to full names)
        if "metal" in field_lower:
            metal_map = {
                "au": "gold",
                "ag": "silver",
                "pt": "platinum",
                "pd": "palladium",
                "gold": "gold",
                "silver": "silver",
                "platinum": "platinum",
                "palladium": "palladium",
            }
            expected_norm = metal_map.get(str(expected).lower(), str(expected).lower())
            actual_norm = metal_map.get(str(actual).lower(), str(actual).lower())
            return expected_norm == actual_norm

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

        # SerialNumber comparison (ignore spaces, hyphens, case)
        if "serial" in field_lower:
            expected_serial = re.sub(r"[\s\-]", "", str(expected).upper())
            actual_serial = re.sub(r"[\s\-]", "", str(actual).upper())
            return expected_serial == actual_serial

        # Default: case-insensitive string comparison
        return str(expected).strip().lower() == str(actual).strip().lower()

    def _weight_matches_combined(
        self,
        expected_weight: Any,
        expected_unit: Any,
        actual_weight: Any,
        actual_unit: Any,
    ) -> bool:
        """Compare weight+unit combined by converting to grams."""
        # Convert expected to grams
        exp_grams = weight_to_grams(expected_weight, expected_unit)
        # Convert actual to grams
        act_grams = weight_to_grams(actual_weight, actual_unit)

        if exp_grams and act_grams:
            return abs(exp_grams - act_grams) < 0.01
        return False
