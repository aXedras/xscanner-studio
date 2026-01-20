"""CLI entry point for strategy benchmarking and testing tool."""

import os

# SET THIS BEFORE ANY OTHER IMPORTS!!!
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"

import argparse  # noqa: E402
from pathlib import Path  # noqa: E402

from .discovery import (  # noqa: E402
    create_strategy,
    find_all_images,
    get_available_strategies,
    list_images_info,
    list_strategies_info,
)
from .runner import run_benchmark


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

    if verbose and result.raw_text:
        print(f"\n📝 Raw Text:\n{result.raw_text}")

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
    for idx, img in enumerate(images[:20], 1):
        try:
            display_path = img.relative_to(Path.cwd()).as_posix()
        except ValueError:
            display_path = str(img)
        print(f"  {idx:2d}. {display_path}")

    if len(images) > 20:
        print(f"  ... and {len(images) - 20} more")

    try:
        img_choice = input("\n🔢 Select image number (or 'q' to quit): ").strip()
        if img_choice.lower() == "q":
            print("👋 Bye!")
            return 0

        img_idx = int(img_choice) - 1
        if img_idx < 0 or img_idx >= len(images):
            print("❌ Invalid selection")
            return 1

        selected_image = images[img_idx]

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

    return run_single_test(selected_image, selected_strategy, verbose=True)


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
        "--map-reduce",
        action="store_true",
        help="Map-reduce: strategies parallel, images sequential. Best for Cloud APIs.",
    )

    parser.add_argument(
        "--ollama-optimized",
        action="store_true",
        help="Ollama-optimized: models sequential, images parallel. Avoids model switching.",
    )

    parser.add_argument(
        "--strategies",
        type=str,
        default=None,
        help="Comma-separated list of strategies to test. "
        "Single: qwen3,qwen3-abl,deepseek,minicpm,llama | "
        "Hybrid: hybrid-minicpm-qwen,hybrid-minicpm-llama,hybrid-llama-qwen",
    )

    parser.add_argument(
        "--quick", action="store_true", help="Quick benchmark: random sample of 3 images"
    )

    parser.add_argument(
        "--difficult-only",
        action="store_true",
        help="Benchmark only on barPictures/difficult folder",
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
