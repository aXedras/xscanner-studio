"""CLI entry point for strategy benchmarking and testing tool."""

import argparse
import logging
import os
from pathlib import Path

from .discovery import (
    create_strategy,
    find_all_images,
    get_available_strategies,
    list_images_info,
    list_strategies_info,
)
from .runner import run_benchmark
from .validator import parse_filename_ground_truth, validate_extraction

# Disable model connectivity checks for CLI (PaddleX)
# Must be set before PaddleOCR is imported (happens in strategies)
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"

# Suppress console INFO/DEBUG output - only show WARNING and above
# This must be done AFTER imports, when handlers are initialized
for handler in logging.root.handlers:
    if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
        handler.setLevel(logging.WARNING)


def run_single_test(image_path: Path, strategy_name: str, verbose: bool = False) -> int:
    """Run a single extraction test on one image with one strategy."""
    if not image_path.exists():
        print(f"❌ Image not found: {image_path}")
        return 1

    try:
        strategy = create_strategy(strategy_name)
    except ValueError as e:
        print(f"❌ {e}")
        strategies = get_available_strategies()
        print(f"Available: {', '.join(strategies.keys())}")
        return 1

    print(f"\n🔍 Testing: {image_path.name}")
    print(f"📊 Strategy: {strategy_name}")
    print(f"{'=' * 60}\n")

    result = strategy.extract(image_path)

    if result.error:
        print(f"❌ Error: {result.error}\n")
        return 1

    print(
        f"✅ Success! (Confidence: {result.confidence:.2%}, Time: {result.processing_time:.2f}s)\n"
    )

    if result.structured_data:
        print("📦 Extracted Data:")
        for key, value in result.structured_data.items():
            print(f"  {key:15s}: {value}")

    # Quality check: validate against filename ground truth
    ground_truth = parse_filename_ground_truth(image_path)
    if ground_truth:
        print("\n🎯 Ground Truth (from filename):")
        for key, value in ground_truth.items():
            if key != "WeightUnit":  # Skip internal field
                print(f"  {key:15s}: {value}")

        successes, errors = validate_extraction(result.structured_data, ground_truth)

        print(f"\n{'=' * 60}")
        print("🔍 Quality Check Results:")
        print(f"{'=' * 60}")

        if successes:
            for success in successes:
                print(f"  {success}")

        if errors:
            print()
            for error in errors:
                print(f"  {error}")

            accuracy = len(successes) / (len(successes) + len(errors)) * 100
            print(
                f"\n📊 Accuracy: {len(successes)}/{len(successes) + len(errors)} fields correct ({accuracy:.1f}%)"
            )
        else:
            print(f"\n🎉 Perfect! All {len(successes)} fields match!")

        print(f"{'=' * 60}")
    else:
        print("\n💡 No ground truth available (filename doesn't match expected pattern)")

    if verbose and result.raw_text:
        print(f"\n📝 Raw Text:\n{result.raw_text}")

    return 0


def run_multiple_tests(image_paths: list[Path], strategy_name: str) -> int:
    """Run extraction tests on multiple images with summary report."""
    try:
        strategy = create_strategy(strategy_name)
    except ValueError as e:
        print(f"❌ {e}")
        strategies = get_available_strategies()
        print(f"Available: {', '.join(strategies.keys())}")
        return 1

    print(f"\n{'=' * 80}")
    print(f"🔬 Batch Testing: {len(image_paths)} images")
    print(f"📊 Strategy: {strategy_name}")
    print(f"{'=' * 80}\n")

    # Statistics tracking
    stats = {
        "total": 0,
        "perfect": 0,
        "with_errors": 0,
        "no_ground_truth": 0,
        "field_errors": {"Metal": 0, "Weight": 0, "Fineness": 0, "Producer": 0, "SerialNumber": 0},
        "processing_times": [],
    }

    # Process each image
    for idx, image_path in enumerate(image_paths, 1):
        print(f"\n[{idx}/{len(image_paths)}] 🔍 {image_path.name}")
        print(f"{'-' * 80}")

        result = strategy.extract(image_path)

        if result.error:
            print(f"❌ Error: {result.error}")
            stats["with_errors"] += 1
            continue

        stats["total"] += 1
        stats["processing_times"].append(result.processing_time)

        print(
            f"✅ Extracted in {result.processing_time:.2f}s (Confidence: {result.confidence:.2%})"
        )

        # Quality check
        ground_truth = parse_filename_ground_truth(image_path)
        if ground_truth:
            successes, errors = validate_extraction(result.structured_data, ground_truth)

            if errors:
                stats["with_errors"] += 1
                print(f"❌ {len(errors)} validation error(s):")
                for error in errors:
                    print(f"  {error}")
                    # Track field errors
                    for field in stats["field_errors"].keys():
                        if field in error:
                            stats["field_errors"][field] += 1
            else:
                stats["perfect"] += 1
                print(f"🎉 Perfect! All {len(successes)} fields match!")
        else:
            stats["no_ground_truth"] += 1
            print("💡 No ground truth available")

    # Summary Report
    print(f"\n{'=' * 80}")
    print("📊 BATCH TEST SUMMARY")
    print(f"{'=' * 80}")

    if stats["total"] == 0:
        print("❌ No images were successfully processed")
        return 1

    perfect = stats["perfect"]
    with_errors = stats["with_errors"]
    total_with_gt = perfect + with_errors
    success_rate = (perfect / total_with_gt * 100) if total_with_gt > 0 else 0

    print("\n🎯 Results:")
    print(f"  • Total processed: {stats['total']}")
    if total_with_gt > 0:
        print(f"  • Perfect extractions: {perfect} ({success_rate:.1f}%)")
        print(f"  • With errors: {with_errors} ({100 - success_rate:.1f}%)")
    if stats["no_ground_truth"] > 0:
        print(f"  • No ground truth: {stats['no_ground_truth']}")

    avg_time = (
        sum(stats["processing_times"]) / len(stats["processing_times"])
        if stats["processing_times"]
        else 0
    )
    total_time = sum(stats["processing_times"])
    print("\n⏱️  Performance:")
    print(f"  • Average time: {avg_time:.2f}s per image")
    print(f"  • Total time: {total_time:.1f}s ({total_time / 60:.1f} minutes)")

    if with_errors > 0:
        print("\n❌ Field-specific Error Rates:")
        for field in ["Metal", "Weight", "Fineness", "Producer", "SerialNumber"]:
            errors = stats["field_errors"][field]
            error_rate = (errors / total_with_gt * 100) if total_with_gt > 0 else 0
            status = "✓" if errors == 0 else "✗"
            print(f"  {status} {field:15s}: {errors:2d} errors ({error_rate:5.1f}%)")

    print(f"\n{'=' * 80}")

    if success_rate == 100:
        print("🎉 EXCELLENT! All extractions were perfect!")
    elif success_rate >= 80:
        print("✅ GOOD! Most extractions successful.")
    elif success_rate >= 50:
        print("⚠️  FAIR. Needs improvement.")
    else:
        print("❌ POOR. Significant issues detected.")

    print(f"{'=' * 80}\n")

    return 0


def interactive_mode() -> int:
    """Interactive menu-driven single test mode."""
    images = find_all_images()

    if not images:
        print("❌ No images found. Please add images to barPictures/ directory.")
        return 1

    strategies = get_available_strategies()

    if not strategies:
        print("❌ No strategies available. Configure API keys in .env.local")
        return 1

    print("\n" + "=" * 60)
    print("🎯 xScanner Interactive Test Tool")
    print("=" * 60)

    # Select image
    print(f"\n📸 Available Images ({len(images)}):\n")
    print(f"   0. [ALL IMAGES] - Test all {len(images)} images")
    for idx, img in enumerate(images, 1):
        try:
            display_path = img.relative_to(Path.cwd()).as_posix()
        except ValueError:
            display_path = str(img)
        print(f"  {idx:2d}. {display_path}")

    try:
        img_choice = input("\n🔢 Select image number (0 for all, or 'q' to quit): ").strip()
        if img_choice.lower() == "q":
            print("👋 Bye!")
            return 0

        img_idx = int(img_choice)

        # Option 0: All images
        if img_idx == 0:
            selected_images = images
        else:
            img_idx -= 1  # Convert to 0-based index
            if img_idx < 0 or img_idx >= len(images):
                print("❌ Invalid selection")
                return 1
            selected_images = [images[img_idx]]

    except (ValueError, KeyboardInterrupt):
        print("\n❌ Invalid input or cancelled")
        return 1

    # Select strategy
    print("\n🤖 Available Strategies:\n")
    strategy_list = list(strategies.keys())
    for idx, name in enumerate(strategy_list, 1):
        print(f"  {idx}. {name}")

    try:
        strat_choice = input("\n🔢 Select strategy number: ").strip()
        strat_idx = int(strat_choice) - 1
        if strat_idx < 0 or strat_idx >= len(strategy_list):
            print("❌ Invalid selection")
            return 1

        selected_strategy = strategy_list[strat_idx]

    except (ValueError, KeyboardInterrupt):
        print("\n❌ Invalid input or cancelled")
        return 1

    # Run tests
    if len(selected_images) == 1:
        # Single image test
        return run_single_test(selected_images[0], selected_strategy, verbose=True)
    else:
        # Multiple images test
        return run_multiple_tests(selected_images, selected_strategy)


def main():
    """Main entry point for benchmark and test tool."""
    parser = argparse.ArgumentParser(
        description="🔬 Strategy Benchmarking and Testing Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
  Benchmark (default)     - Compare all strategies on multiple images
  Single test             - Test one strategy on one image
  Interactive             - Menu-driven single test
  List                    - Show images or strategies

Examples:
  python -m tools.cli.cli                           # Full benchmark
  python -m tools.cli.cli --quick                   # Quick benchmark (3 images)
  python -m tools.cli.cli --interactive             # Interactive mode
  python -m tools.cli.cli --image bar.jpg --strategy chatgpt
  python -m tools.cli.cli --list-images
  python -m tools.cli.cli --list-strategies
        """,
    )

    # Benchmark options
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Number of parallel strategy workers per image (benchmark mode)",
    )

    parser.add_argument(
        "--image-workers",
        type=int,
        default=None,
        help="Number of images to process in parallel (benchmark mode)",
    )

    parser.add_argument(
        "--quick", action="store_true", help="Quick benchmark: random sample of 3 images"
    )

    # Single test options
    parser.add_argument("--image", type=Path, help="Path to image file (single test mode)")

    parser.add_argument(
        "--strategy",
        choices=["chatgpt", "gemini", "hybrid"],
        help="Strategy to use (single test mode)",
    )

    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Show verbose output including raw text"
    )

    # Mode selection
    parser.add_argument(
        "-i", "--interactive", action="store_true", help="Interactive menu-driven test mode"
    )

    parser.add_argument("--list-images", action="store_true", help="List all test images")

    parser.add_argument("--list-strategies", action="store_true", help="List available strategies")

    args = parser.parse_args()

    # List modes
    if args.list_images:
        list_images_info()
        return 0

    if args.list_strategies:
        list_strategies_info()
        return 0

    # Interactive mode
    if args.interactive:
        return interactive_mode()

    # Single test mode
    if args.image and args.strategy:
        return run_single_test(args.image, args.strategy, args.verbose)

    if args.image and not args.strategy:
        print("❌ --image requires --strategy")
        return 1

    # Default: benchmark mode
    return run_benchmark(args)


if __name__ == "__main__":
    exit(main())
