"""Execution management for parallel and sequential strategy runs."""

import os
import signal
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from xscanner.strategy.base import ExtractionResult, ExtractionStrategy

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


def is_shutdown_requested() -> bool:
    """Check if graceful shutdown has been requested."""
    return _shutdown_requested


def reset_shutdown_flag():
    """Reset the shutdown flag (call at start of new run)."""
    global _shutdown_requested
    _shutdown_requested = False


def run_strategy_safe(strategy: ExtractionStrategy, image_path: Path) -> ExtractionResult:
    """Execute strategy with error handling.

    Args:
        strategy: The extraction strategy to run
        image_path: Path to the image file

    Returns:
        ExtractionResult (with error field populated if execution failed)
    """
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


def run_strategies_sequential(
    strategies: list[ExtractionStrategy], image_path: Path
) -> dict[str, ExtractionResult]:
    """Execute strategies one by one.

    Args:
        strategies: List of strategies to execute
        image_path: Path to the image file

    Returns:
        Dictionary mapping strategy name to result
    """
    results: dict[str, ExtractionResult] = {}
    print(f"\n{'=' * 80}")
    print(f"Testing: {image_path.name}")
    print(f"{'=' * 80}")

    for strategy in strategies:
        print(f"\n  Running {strategy.name}...", end=" ")
        result = run_strategy_safe(strategy, image_path)
        results[strategy.name] = result

        if result.error:
            print(f"❌ Error: {result.error}")
        else:
            print(f"✓ Done ({result.processing_time:.2f}s)")

    return results


def run_strategies_parallel(
    strategies: list[ExtractionStrategy], image_path: Path, worker_count: int
) -> dict[str, ExtractionResult]:
    """Execute strategies in parallel using ThreadPoolExecutor.

    Args:
        strategies: List of strategies to execute
        image_path: Path to the image file
        worker_count: Number of parallel workers to use

    Returns:
        Dictionary mapping strategy name to result (in original strategy order)
    """
    print(f"\n{'=' * 80}")
    print(f"Testing: {image_path.name}")
    print(f"{'=' * 80}")
    print(f"\n  Executing with {worker_count} parallel workers...")

    completion: dict[str, ExtractionResult] = {}
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        future_map = {
            executor.submit(run_strategy_safe, strategy, image_path): strategy
            for strategy in strategies
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
    for strategy in strategies:
        strategy_result: ExtractionResult | None = completion.get(strategy.name)
        if strategy_result is not None:
            ordered_results[strategy.name] = strategy_result
    return ordered_results
