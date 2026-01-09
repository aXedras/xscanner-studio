"""Benchmark runner logic."""

import random
from datetime import datetime
from pathlib import Path

from .comparator import OCRComparator, _shutdown_requested


def run_benchmark(args) -> int:
    """Run full benchmark comparing all strategies on multiple images."""
    from xscanner.server.config import get_config
    from xscanner.strategy.chatgpt_vision_strategy import ChatGPTVisionStrategy
    from xscanner.strategy.gemini_flash_strategy import GeminiFlashStrategy

    config = get_config()

    # Initialize available strategies
    strategies = []

    if config.openai.api_key:
        strategies.append(ChatGPTVisionStrategy(config))

    if config.google.api_key:
        strategies.append(GeminiFlashStrategy(config))

    if not strategies:
        print("❌ No OCR strategies available!")
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

    print("🔬 Starting OCR Strategy Benchmark")
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
    comparator = OCRComparator(
        strategies=strategies, max_workers=args.workers, image_workers=args.image_workers
    )

    print("\n🚀 Starting benchmark...\n")

    for img_path in test_images:
        if _shutdown_requested:
            print("\n⚠️  Benchmark interrupted by user")
            break

        results = comparator.test_image(img_path)

        # Store results in format expected by report
        comparator.results.append(
            {
                "image": str(img_path),
                "timestamp": datetime.now().isoformat(),
                "results": {name: result.__dict__ for name, result in results.items()},
            }
        )

    # Save results
    output_file = Path("reports/strategy_benchmark_results.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    comparator.save_results(output_file)

    print("\n✅ Benchmark complete!")
    print(f"📊 Results saved to: {output_file}")
    print("\n💡 Generate report: make benchmark-report")

    return 0
