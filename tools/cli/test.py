#!/usr/bin/env python3
"""Interactive OCR testing tool for xScanner

Usage:
    python -m cli.test                    # Interactive mode
    python -m cli.test --list-images      # List available images
    python -m cli.test --list-strategies  # List OCR strategies
    python -m cli.test --image path.jpg --strategy chatgpt  # Direct test
    python -m cli.test --help             # Show this help
"""

import argparse
from pathlib import Path

from xscanner.server.config import get_config
from xscanner.strategy.base import OCRStrategy
from xscanner.strategy.chatgpt_vision_strategy import ChatGPTVisionStrategy
from xscanner.strategy.gemini_flash_strategy import GeminiFlashStrategy
from xscanner.strategy.paddle_llama_hybrid_strategy import PaddleLlamaHybridStrategy

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png")
SEARCH_PATHS = [
    Path("barPictures") / "Renamed-and-Sorted Au, Ag, Pt",
    Path("barPictures") / "difficult",
    Path("barPictures"),
    Path("invoices"),
]


def find_all_images() -> list[Path]:
    """Find all image files in standard locations"""
    images = []
    seen = set()

    for search_path in SEARCH_PATHS:
        if not search_path.exists():
            continue
        for img_path in search_path.rglob("*"):
            if img_path.suffix.lower() in IMAGE_EXTENSIONS:
                key = str(img_path.resolve())
                if key not in seen:
                    seen.add(key)
                    images.append(img_path)

    return sorted(images)


def get_available_strategies() -> dict[str, type[OCRStrategy]]:
    """Get map of strategy names to classes"""
    config = get_config()

    strategies: dict[str, type[OCRStrategy]] = {}

    # ChatGPT (always available if API key configured)
    if config.openai.api_key:
        strategies["chatgpt"] = ChatGPTVisionStrategy

    # Gemini (if API key configured)
    if config.google.api_key:
        strategies["gemini"] = GeminiFlashStrategy

    # Local Hybrid (PaddleOCR + Llama)
    strategies["hybrid"] = PaddleLlamaHybridStrategy

    return strategies


def list_images():
    """List all available images"""
    images = find_all_images()

    if not images:
        print("❌ No images found in standard locations")
        print("\nSearched in:")
        for path in SEARCH_PATHS:
            print(f"  - {path}")
        return

    print(f"\n📸 Found {len(images)} images:\n")
    for idx, img in enumerate(images, 1):
        # Try to extract info from filename
        name = img.stem
        size_kb = img.stat().st_size / 1024
        try:
            display_path = img.relative_to(Path.cwd())
        except ValueError:
            display_path = img
        print(f"  {idx:3d}. {display_path} ({size_kb:.1f} KB)")
        if "_" in name:
            print(f"       → {name}")


def list_strategies():
    """List available OCR strategies"""
    strategies = get_available_strategies()

    if not strategies:
        print("❌ No strategies available. Check your API keys in .env.local")
        return

    print(f"\n🤖 Available OCR Strategies ({len(strategies)}):\n")
    for name in strategies:
        print(f"  - {name}")

    config = get_config()
    print("\n💡 Configuration:")
    print(f"  OpenAI API Key: {'✅ Configured' if config.openai.api_key else '❌ Missing'}")
    print(f"  Google API Key: {'✅ Configured' if config.google.api_key else '❌ Missing'}")
    print(f"  Ollama URL: {config.ollama.base_url}")


def run_test(image_path: Path, strategy_name: str, verbose: bool = False):
    """Run OCR test on single image"""
    strategies = get_available_strategies()

    if strategy_name not in strategies:
        print(f"❌ Strategy '{strategy_name}' not available")
        print(f"Available: {', '.join(strategies.keys())}")
        return 1

    if not image_path.exists():
        print(f"❌ Image not found: {image_path}")
        return 1

    print(f"\n🔍 Testing: {image_path.name}")
    print(f"📊 Strategy: {strategy_name}")
    print(f"{'=' * 60}\n")

    # Initialize strategy
    config = get_config()
    strategy_class = strategies[strategy_name]

    strategy: OCRStrategy
    if strategy_name == "chatgpt":
        strategy = ChatGPTVisionStrategy(
            api_key=config.openai.api_key,
            model=config.openai.model,
        )
    elif strategy_name == "gemini":
        strategy = GeminiFlashStrategy(api_key=config.google.api_key)
    elif strategy_name == "hybrid":
        strategy = PaddleLlamaHybridStrategy(base_url=config.ollama.base_url)
    else:
        strategy = strategy_class()

    # Run extraction
    result = strategy.extract(image_path)

    # Display results
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


def interactive_mode():
    """Interactive menu-driven mode"""
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

    # Step 1: Select image
    print(f"\n📸 Available Images ({len(images)}):\n")
    for idx, img in enumerate(images[:20], 1):  # Show first 20
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

    # Step 2: Select strategy
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

    # Run test
    return run_test(selected_image, selected_strategy, verbose=True)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Interactive OCR testing tool for xScanner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m cli.test                              # Interactive mode
  python -m cli.test --list-images                # List all images
  python -m cli.test --list-strategies            # List OCR strategies
  python -m cli.test --image path.jpg --strategy chatgpt
        """,
    )

    parser.add_argument("--list-images", action="store_true", help="List all available test images")

    parser.add_argument(
        "--list-strategies", action="store_true", help="List available OCR strategies"
    )

    parser.add_argument("--image", type=Path, help="Path to image file to test")

    parser.add_argument(
        "--strategy", choices=["chatgpt", "gemini", "hybrid"], help="OCR strategy to use"
    )

    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Show verbose output including raw text"
    )

    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Force interactive mode (default if no args)",
    )

    args = parser.parse_args()

    # List modes
    if args.list_images:
        list_images()
        return 0

    if args.list_strategies:
        list_strategies()
        return 0

    # Direct test mode
    if args.image and args.strategy:
        return run_test(args.image, args.strategy, args.verbose)

    if args.image and not args.strategy:
        print("❌ --image requires --strategy")
        return 1

    # Default to interactive mode
    return interactive_mode()


if __name__ == "__main__":
    raise SystemExit(main())
