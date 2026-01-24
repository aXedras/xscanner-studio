"""Benchmark runner logic.

This runner benchmarks the strategies supported by the CLI:
- Cloud: ChatGPT Vision, Gemini Flash (when API keys are configured)
- Local: LoRA fine-tuned (only local strategy)
"""

import os
import random
import re
from pathlib import Path

from .comparator import StrategyComparator  # noqa: E402

_BENCH_STRATEGY_NAMES = ("lora", "chatgpt", "gemini")


def get_benchmark_image_pool(*, difficult_only: bool) -> list[Path]:
    """Return the list of images eligible for benchmarking."""
    if difficult_only:
        search_paths = [Path("barPictures/difficult")]
    else:
        # Keep compatibility with historical folder names.
        renamed_sorted_candidates = [
            Path("barPictures") / "Renamed-and-Sorted Au, Ag, Pt",
            Path("barPictures") / "Renamed-and-Sorted",
        ]
        renamed_sorted = next((p for p in renamed_sorted_candidates if p.exists()), None)

        search_paths = [Path("barPictures/difficult")]
        if renamed_sorted is not None:
            search_paths.append(renamed_sorted)

    all_images: list[Path] = []
    for base_path in search_paths:
        if base_path.exists():
            all_images.extend(base_path.rglob("*.jpg"))
            all_images.extend(base_path.rglob("*.jpeg"))
            all_images.extend(base_path.rglob("*.png"))

    return all_images


def _parse_requested_benchmark_strategies(args) -> list[str] | None:
    raw = getattr(args, "strategies", None)
    if not raw:
        return None

    requested = [s.strip().lower() for s in str(raw).split(",") if s.strip()]
    if not requested:
        return None

    unknown = [s for s in requested if s not in _BENCH_STRATEGY_NAMES]
    if unknown:
        unknown_str = ", ".join(sorted(set(unknown)))
        allowed_str = ", ".join(_BENCH_STRATEGY_NAMES)
        raise ValueError(f"Unknown strategy name(s): {unknown_str}. Allowed: {allowed_str}")

    # De-dup while preserving order
    seen: set[str] = set()
    ordered: list[str] = []
    for s in requested:
        if s not in seen:
            seen.add(s)
            ordered.append(s)

    return ordered


def _get_requested_sample_size(args) -> int | None:
    raw = getattr(args, "sample_size", None)
    if raw is None:
        return None
    try:
        value = int(raw)
    except Exception:
        return None
    return value if value > 0 else None


def parse_filename_metadata(image_path: Path) -> dict[str, any] | None:
    """Extract expected metadata from filename.

    Expected pattern: Metal_WeightFineness_SerialNumber_Producer.jpg
    Example: Gold_01000g_9999_AB55223_CS.jpg

    Returns:
        Dictionary with expected fields or None if pattern doesn't match
    """
    # Pattern: Metal_WeightUnit_Fineness_Serial_Producer.ext
    # Example: Gold_01000g_9999_AB55223_CS.jpg
    #          Silver_00100g_9990_12345_Heraeus.jpg
    pattern = r"^([A-Za-z]+)_(\d+)([a-z]+)_(\d+)_([A-Za-z0-9]+)_(.+)\.(jpg|jpeg|png)$"

    match = re.match(pattern, image_path.name, re.IGNORECASE)
    if not match:
        return None

    metal, weight, unit, fineness, serial, producer_raw, _ = match.groups()

    # Clean producer (remove extension if any)
    producer = producer_raw.replace(".jpg", "").replace(".jpeg", "").replace(".png", "")
    producer = producer.replace("_", " ").strip()

    # Normalize metal name
    metal_map = {
        "gold": "Gold",
        "silver": "Silver",
        "ag": "Silver",
        "au": "Gold",
        "platinum": "Platinum",
        "pt": "Platinum",
        "palladium": "Palladium",
        "pd": "Palladium",
    }
    metal_normalized = metal_map.get(metal.lower(), metal.capitalize())

    # Format fineness (add decimal point: 9999 -> 999.9)
    if len(fineness) == 4:
        fineness_value = f"{fineness[0:3]}.{fineness[3]}"
    else:
        fineness_value = fineness

    return {
        "source": "filename",
        "fields": {
            "Metal": metal_normalized,
            "Weight": weight.lstrip("0") or "0",
            "WeightUnit": unit,
            "Fineness": fineness_value,
            "SerialNumber": serial,
            "Producer": producer,
        },
    }


def run_benchmark(args) -> int:
    """Run benchmark comparing all available strategies on multiple images."""

    from xscanner.strategy.chatgpt_vision_strategy import ChatGPTVisionStrategy
    from xscanner.strategy.gemini_flash_strategy import GeminiFlashStrategy
    from xscanner.strategy.lora_finetuned_strategy import LoRAFinetunedStrategy

    try:
        requested = _parse_requested_benchmark_strategies(args)
    except ValueError as exc:
        print(f"❌ {exc}")
        return 1

    strategies = []
    print("🔧 Initializing strategies...")
    print("=" * 60)

    if requested is not None:
        print(f"Requested: {', '.join(requested)}")

    # Initialize in requested order, or in stable default order.
    to_init = requested if requested is not None else ["chatgpt", "gemini", "lora"]

    for name in to_init:
        if name == "chatgpt":
            if not os.environ.get("OPENAI_API_KEY"):
                print("⚠ ChatGPT Vision skipped: OPENAI_API_KEY not set")
                continue
            try:
                strategies.append(ChatGPTVisionStrategy())
                print("✓ ChatGPT Vision")
            except Exception as exc:
                print(f"⚠️  ChatGPT skipped: {exc}")
            continue

        if name == "gemini":
            if not os.environ.get("GOOGLE_API_KEY"):
                print("⚠ Gemini Flash skipped: GOOGLE_API_KEY not set")
                continue
            try:
                strategies.append(GeminiFlashStrategy())
                print("✓ Gemini Flash")
            except Exception as exc:
                print(f"⚠️  Gemini skipped: {exc}")
            continue

        if name == "lora":
            base_url = os.environ.get("LORA_BASE_URL")
            if not base_url:
                try:
                    from xscanner.server.config import get_config

                    base_url = get_config().lora.base_url
                except Exception:
                    base_url = None

            if base_url and LoRAFinetunedStrategy.is_available(base_url):
                try:
                    strategies.append(LoRAFinetunedStrategy(base_url=base_url))
                    print("✓ LoRA Fine-tuned")
                except Exception as exc:
                    print(f"⚠️  LoRA skipped: {exc}")
            else:
                if base_url:
                    print("⚠ LoRA skipped: service not reachable")
                else:
                    print("⚠ LoRA skipped: LORA_BASE_URL not configured")
            continue

    print("=" * 60)

    if not strategies:
        print("\n❌ No strategies available!")
        print("💡 Set OPENAI_API_KEY and/or GOOGLE_API_KEY for cloud strategies")
        print("💡 Set LORA_BASE_URL for local LoRA strategy")
        return 1

    # Find test images
    difficult_only = bool(getattr(args, "difficult_only", False))
    all_images = get_benchmark_image_pool(difficult_only=difficult_only)

    if not all_images:
        print("\n❌ No test images found!")
        return 1

    # Select images based on mode
    requested_sample_size = _get_requested_sample_size(args)
    if requested_sample_size is not None:
        test_images = random.sample(all_images, min(requested_sample_size, len(all_images)))
        mode = f"SAMPLE ({len(test_images)} random images)"
    elif args.quick:
        test_images = random.sample(all_images, min(3, len(all_images)))
        mode = "QUICK (3 random images)"
    else:
        test_images = all_images
        mode = f"FULL ({len(all_images)} images)"

    exec_mode = "STANDARD"

    print("🔬 Starting strategy benchmark")
    print("=" * 60)
    print(f"Mode: {mode}")
    print(f"Execution: {exec_mode}")
    print(f"Strategies: {len(strategies)}")
    print(f"Images: {len(test_images)}")
    print(f"Workers: {args.workers or 'auto'}")
    print(f"Image workers: {args.image_workers or 'auto'}")
    print("=" * 60)

    if args.quick:
        print("\n📸 Selected images:")
        for img in test_images:
            print(f"  - {img.name}")

    # Prepare image cases with expected metadata where available
    image_cases = []
    for img_path in test_images:
        expected = parse_filename_metadata(img_path)
        if expected:
            image_cases.append({"image": img_path, "expected": expected})
        else:
            # No expected data (e.g., difficult folder)
            image_cases.append(img_path)

    # Run benchmark
    comparator = StrategyComparator(
        strategies=strategies, max_workers=args.workers, image_workers=args.image_workers
    )

    print("\n🚀 Starting benchmark...\n")

    comparator.test_multiple_images(image_cases)

    # Save results (JSON + CSV) and keep a timestamped history copy
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    output_file = Path("reports/strategy_benchmark_results.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    comparator.save_results(output_file)

    # Also save CSV for easy human review
    csv_file = output_file.with_suffix(".csv")
    comparator.save_results_csv(csv_file)

    # Save historical copy with timestamp (for history index)
    history_dir = Path("reports/history")
    history_dir.mkdir(parents=True, exist_ok=True)
    history_file = history_dir / f"strategy_benchmark_results_{timestamp}.json"
    comparator.save_results(history_file)

    print(f"📊 Results saved to: {output_file}")
    print(f"📊 CSV saved to: {csv_file}")
    print(f"📁 History saved to: {history_file}")

    print("\n📊 Updating HTML reports + history index...")
    try:
        from .report import generate_reports

        generate_reports()
    except Exception as exc:
        print(f"⚠️  Report generation failed: {exc}")
        print("💡 You can retry with: make cli-report-history")

    return 0
