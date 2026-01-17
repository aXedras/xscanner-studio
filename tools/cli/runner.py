"""Benchmark runner logic."""

import random
from pathlib import Path

from .comparator import StrategyComparator


def run_benchmark(args) -> int:
    """Run full benchmark comparing all strategies on multiple images."""
    from xscanner.server.config import get_config
    from xscanner.strategy.chatgpt_vision_strategy import ChatGPTVisionStrategy
    from xscanner.strategy.gemini_flash_strategy import GeminiFlashStrategy

    config = get_config()

    # Initialize available strategies
    strategies = []

    if config.openai.api_key:
        strategies.append(
            ChatGPTVisionStrategy(
                api_key=config.openai.api_key,
                model=config.openai.model,
                temperature=config.openai.temperature,
                max_output_tokens=config.openai.max_output_tokens,
            )
        )

    if config.google.api_key:
        strategies.append(
            GeminiFlashStrategy(
                api_key=config.google.api_key,
                model=config.google.model,
            )
        )

    if not strategies:
        print("❌ No strategies available!")
        print("💡 Set OPENAI_API_KEY or GOOGLE_API_KEY in .env.local")
        return 1

    # Find test images
    search_paths = [
        Path("barPictures/Renamed-and-Sorted Au, Ag, Pt"),
        Path("barPictures/difficult"),
    ]

    all_images = []
    for base_path in search_paths:
        if base_path.exists():
            all_images.extend(base_path.rglob("*.jpg"))
            all_images.extend(base_path.rglob("*.jpeg"))
            all_images.extend(base_path.rglob("*.png"))

    if not all_images:
        print("❌ No test images found!")
        return 1

    # Select images based on mode
    if args.quick:
        test_images = random.sample(all_images, min(3, len(all_images)))
        mode = "QUICK (3 random images)"
    else:
        test_images = all_images
        mode = "FULL"

    print("🔬 Starting strategy benchmark")
    print("=" * 60)
    print(f"Mode: {mode}")
    print(f"Strategies: {len(strategies)}")
    print(f"Images: {len(test_images)}")
    print(f"Workers: {args.workers or 'auto'}")
    print(f"Image workers: {args.image_workers or 'auto'}")
    print("=" * 60)

    if args.quick:
        print("\n📸 Selected images:")
        for img in test_images:
            print(f"  - {img.name}")
    # Run benchmark
    comparator = StrategyComparator(
        strategies=strategies, max_workers=args.workers, image_workers=args.image_workers
    )

    print("\n🚀 Starting benchmark...\n")

    # Let comparator manage sequential vs parallel processing and result ordering.
    comparator.test_multiple_images(test_images)

    # Save results
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save current results (for report generation)
    output_file = Path("reports/strategy_benchmark_results.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    comparator.save_results(output_file)

    # Save historical copy with timestamp
    history_dir = Path("reports/history")
    history_dir.mkdir(parents=True, exist_ok=True)
    history_file = history_dir / f"strategy_benchmark_results_{timestamp}.json"
    comparator.save_results(history_file)

    print(f"📊 Results saved to: {output_file}")
    print(f"📁 History saved to: {history_file}")
    print("\n💡 Generate report: make cli-report")

    return 0
