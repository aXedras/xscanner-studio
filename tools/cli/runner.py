"""Benchmark runner logic.

This runner benchmarks the strategies supported by the CLI:
- Cloud: ChatGPT Vision, ChatGPT 2-Stage (V1 & V2), Gemini Flash
- LoRA: LoRA fine-tuned, LoRA 2-Stage
"""

import os
import random
import re
from pathlib import Path

from .comparator import StrategyComparator  # noqa: E402

_BENCH_STRATEGY_NAMES = (
    "chatgpt",
    "chatgpt-2stage",
    "gemini",
    "lora",
    "lora-2stage",
)


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

    Supported patterns:
    1. Standard: Gold_01000g_9999_AB55223_CS.jpg
    2. TroyOunce: Silver_979.40troyounce_9990_4184903_Asahi_.jpeg

    Returns:
        Dictionary with expected fields or None if pattern doesn't match
    """
    # Pattern 1: Standard format (whole number weight)
    # Example: Gold_01000g_9999_AB55223_CS.jpg
    #          Silver_00100g_9990_12345_Heraeus.jpg
    standard_pattern = r"^([A-Za-z]+)_(\d+)([a-z]+)_(\d+)_([A-Za-z0-9]+)_(.+)\.(jpg|jpeg|png)$"

    # Pattern 2: TroyOunce format (decimal weight)
    # Example: Silver_979.40troyounce_9990_4184903_Asahi_.jpeg
    troyounce_pattern = (
        r"^([A-Za-z]+)_(\d+\.\d+)(troyounce)_(\d+)_([A-Za-z0-9]+)_(.+)\.(jpg|jpeg|png)$"
    )

    match = re.match(standard_pattern, image_path.name, re.IGNORECASE)
    if not match:
        match = re.match(troyounce_pattern, image_path.name, re.IGNORECASE)

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

    # Normalize weight unit
    unit_lower = unit.lower()
    unit_map = {
        "g": "g",
        "kg": "kg",
        "toz": "toz",
        "oz": "oz",
        "troyounce": "toz",  # Convert troyounce → toz
    }
    unit_normalized = unit_map.get(unit_lower, unit_lower)

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
            "WeightUnit": unit_normalized,
            "Fineness": fineness_value,
            "SerialNumber": serial,
            "Producer": producer,
        },
    }


def run_benchmark(args) -> int:
    """Run benchmark comparing all available strategies on multiple images."""

    from xscanner.strategy.chatgpt_2stage_vision_strategy import ChatGPT2StageVisionStrategy
    from xscanner.strategy.chatgpt_vision_strategy import ChatGPTVisionStrategy
    from xscanner.strategy.gemini_flash_strategy import GeminiFlashStrategy
    from xscanner.strategy.lora_2stage_strategy import LoRA2StageStrategy
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
    to_init = (
        requested
        if requested is not None
        else ["chatgpt", "chatgpt-2stage", "gemini", "lora", "lora-2stage"]
    )

    for name in to_init:
        # ChatGPT strategies
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

        if name == "chatgpt-2stage":
            if not os.environ.get("OPENAI_API_KEY"):
                print("⚠ ChatGPT 2-Stage skipped: OPENAI_API_KEY not set")
                continue
            try:
                strategies.append(ChatGPT2StageVisionStrategy())
                print("✓ ChatGPT 2-Stage (V1)")
            except Exception as exc:
                print(f"⚠️  ChatGPT 2-Stage skipped: {exc}")
            continue

        # Gemini
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

        # LoRA strategies
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

        if name == "lora-2stage":
            base_url = os.environ.get("LORA_BASE_URL")
            if not base_url:
                try:
                    from xscanner.server.config import get_config

                    base_url = get_config().lora.base_url
                except Exception:
                    base_url = None

            if base_url and LoRA2StageStrategy.is_available(base_url):
                try:
                    strategies.append(LoRA2StageStrategy(base_url=base_url))
                    print("✓ LoRA 2-Stage")
                except Exception as exc:
                    print(f"⚠️  LoRA 2-Stage skipped: {exc}")
            else:
                if base_url:
                    print("⚠ LoRA 2-Stage skipped: service not reachable")
                else:
                    print("⚠ LoRA 2-Stage skipped: LORA_BASE_URL not configured")
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
        # Always include troyounce images (priority images)
        troyounce_images = [img for img in all_images if "troyounce" in img.name.lower()]
        other_images = [img for img in all_images if "troyounce" not in img.name.lower()]

        # Start with all troyounce images
        test_images = list(troyounce_images)

        # Fill remaining slots with random other images
        remaining_slots = requested_sample_size - len(test_images)
        if remaining_slots > 0 and other_images:
            random_others = random.sample(other_images, min(remaining_slots, len(other_images)))
            test_images.extend(random_others)

        # Shuffle to avoid always testing troyounce first
        random.shuffle(test_images)

        troyounce_count = len(troyounce_images)
        mode = f"SAMPLE ({len(test_images)} images: {troyounce_count} troyounce + {len(test_images) - troyounce_count} random)"
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

    # Output file for incremental saves
    output_file = Path("reports/strategy_benchmark_results.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Run with incremental saving (saves after each image)
    comparator.test_multiple_images(image_cases, incremental_save_path=output_file)

    # Save results (JSON + CSV) and keep a timestamped history copy
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

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
