"""Benchmark runner logic."""

import os
import random
import re
from pathlib import Path

import requests

# Disable PaddleOCR model source check BEFORE any imports
os.environ["DISABLE_MODEL_SOURCE_CHECK"] = "True"

from .comparator import StrategyComparator  # noqa: E402


def warmup_ollama_models(
    models: list[str], base_url: str = "http://localhost:11434"
) -> dict[str, bool]:
    """Pre-load models into Ollama memory to avoid timeout during benchmark.

    Args:
        models: List of model names to warm up (e.g., ["qwen3-vl:latest", "minicpm-v:latest"])
        base_url: Ollama API base URL

    Returns:
        Dictionary with model name -> success status
    """
    results = {}

    for model in models:
        print(f"  🔥 Warming up {model}...", end=" ", flush=True)
        try:
            # Use the generate endpoint with an empty prompt to load the model
            # keep_alive=-1 keeps model loaded indefinitely
            response = requests.post(
                f"{base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": "Hello",  # Minimal prompt just to load model
                    "stream": False,
                    "keep_alive": -1,  # Keep model loaded indefinitely
                    "options": {"num_predict": 1},  # Generate minimal output
                },
                timeout=600,  # 10 min for cold load
            )
            response.raise_for_status()
            results[model] = True
            print("✅ loaded")
        except requests.exceptions.Timeout:
            results[model] = False
            print("⚠️ timeout (will retry during benchmark)")
        except requests.exceptions.ConnectionError:
            results[model] = False
            print("❌ Ollama not running")
        except Exception as e:
            results[model] = False
            print(f"❌ {e}")

    return results


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


def _check_hybrid_available(strategy_class) -> bool:
    """Check if a hybrid strategy is available (both models must be present)."""
    try:
        # V2 hybrids have class method is_available()
        if hasattr(strategy_class, "is_available"):
            return strategy_class.is_available()
        # Legacy hybrids need instance check
        instance = strategy_class()
        primary_available = instance.primary_strategy.is_available()
        secondary_available = instance.secondary_strategy.is_available()
        return primary_available and secondary_available
    except Exception:
        return False


def run_benchmark(args) -> int:
    """Run full benchmark comparing all strategies on multiple images."""
    # Cloud strategies
    from xscanner.strategy.chatgpt_vision_strategy import ChatGPTVisionStrategy
    from xscanner.strategy.gemini_flash_strategy import GeminiFlashStrategy

    # Hybrid strategies (from refactored package)
    from xscanner.strategy.hybrid import (
        MiniCPMQwenHybridV2,
        MiniCPMQwenHybridV3,
        QwenMiniCPMHybridV2,
        QwenMiniCPMHybridV3,
    )

    # LoRA fine-tuned model
    from xscanner.strategy.lora_finetuned_strategy import LoRAFinetunedStrategy

    # Single model strategies
    from xscanner.strategy.minicpm_v_strategy import MiniCPMVStrategy
    from xscanner.strategy.qwen3_vision_strategy import Qwen3VisionStrategy

    # Legacy hybrid (optional - in archive)
    try:
        from xscanner.strategy.archive.vision_hybrid_strategies import (
            MiniCPMQwenHybridStrategy,
        )

        LEGACY_HYBRID_AVAILABLE = True
    except ImportError:
        MiniCPMQwenHybridStrategy = None
        LEGACY_HYBRID_AVAILABLE = False

    # Config removed - not needed for benchmark

    # Parse strategy filter if provided
    strategy_filter = None
    if hasattr(args, "strategies") and args.strategies:
        strategy_filter = [s.strip().lower() for s in args.strategies.split(",")]
        print(f"\n🎯 Strategy filter: {', '.join(strategy_filter)}")

    # Strategy name mapping - single models
    # NOTE: Llama 3.2 Vision removed due to poor performance (1.9% Fineness/Producer accuracy)
    # NOTE: Qwen3-VL Abliterated removed - not actively used
    STRATEGY_MAP = {
        "qwen3": ("Qwen3VisionStrategy", Qwen3VisionStrategy, "Qwen3-VL"),
        "minicpm": ("MiniCPMVStrategy", MiniCPMVStrategy, "MiniCPM-V"),
        # LoRA fine-tuned
        "lora": ("LoRAFinetunedStrategy", LoRAFinetunedStrategy, "LoRA Fine-tuned"),
        # Cloud strategies
        "chatgpt": ("ChatGPTVisionStrategy", ChatGPTVisionStrategy, "ChatGPT-4o"),
        "gemini": ("GeminiFlashStrategy", GeminiFlashStrategy, "Gemini Flash"),
    }

    # Hybrid strategies V2 - intelligent conditional execution
    # NOTE: Llama-based hybrids removed due to poor Llama performance
    HYBRID_STRATEGY_MAP = {
        "hybrid-v2-qwen-first": ("QwenMiniCPMHybridV2", QwenMiniCPMHybridV2, "Qwen → MiniCPM (V2)"),
        "hybrid-v2-minicpm-first": (
            "MiniCPMQwenHybridV2",
            MiniCPMQwenHybridV2,
            "MiniCPM → Qwen (V2)",
        ),
        # V3 - Always both models, smart merge (Fineness always MiniCPM)
        "hybrid-v3-qwen-first": ("QwenMiniCPMHybridV3", QwenMiniCPMHybridV3, "Qwen + MiniCPM (V3)"),
        "hybrid-v3-minicpm-first": (
            "MiniCPMQwenHybridV3",
            MiniCPMQwenHybridV3,
            "MiniCPM + Qwen (V3)",
        ),
    }

    # Add legacy hybrid only if available
    if LEGACY_HYBRID_AVAILABLE and MiniCPMQwenHybridStrategy:
        HYBRID_STRATEGY_MAP["hybrid"] = (
            "MiniCPMQwenHybridStrategy",
            MiniCPMQwenHybridStrategy,
            "MiniCPM → Qwen (Legacy)",
        )

    # Determine which models need to be warmed up based on strategy filter
    models_to_warmup = set()
    if strategy_filter:
        for key in strategy_filter:
            if key in [
                "qwen3",
                "hybrid-v2-qwen-first",
                "hybrid-v2-minicpm-first",
                "hybrid-v3-qwen-first",
                "hybrid-v3-minicpm-first",
                "hybrid",
            ]:
                models_to_warmup.add("qwen3-vl:latest")
            if key in [
                "minicpm",
                "hybrid-v2-qwen-first",
                "hybrid-v2-minicpm-first",
                "hybrid-v3-qwen-first",
                "hybrid-v3-minicpm-first",
                "hybrid",
            ]:
                models_to_warmup.add("minicpm-v:latest")
    else:
        # No filter = all models
        models_to_warmup = {"qwen3-vl:latest", "minicpm-v:latest"}

    # Warm up models BEFORE benchmark to avoid cold-start timeouts
    if models_to_warmup:
        print("\n🔥 Pre-loading models into Ollama memory...")
        print("   (This prevents timeout during model switching)")
        warmup_results = warmup_ollama_models(list(models_to_warmup))

        if not any(warmup_results.values()):
            print("\n❌ No models could be loaded. Is Ollama running?")
            print("💡 Start Ollama: ollama serve")
            return 1
        print()

    # Initialize available strategies
    strategies = []
    print("🔧 Initializing strategies...")
    print("=" * 60)

    # Single-model strategies
    for key, (_class_name, strategy_class, display_name) in STRATEGY_MAP.items():
        # Skip if not in filter
        if strategy_filter and key not in strategy_filter:
            continue

        try:
            if strategy_class.is_available():
                strategies.append(strategy_class())
                print(f"✓ {display_name}")
            else:
                print(f"⚠ {display_name} model not found in Ollama")
        except Exception as e:
            print(f"⚠️  {display_name} skipped: {e}")

    # Hybrid strategies
    for key, (_class_name, strategy_class, display_name) in HYBRID_STRATEGY_MAP.items():
        # Skip if not in filter
        if strategy_filter and key not in strategy_filter:
            continue

        try:
            if _check_hybrid_available(strategy_class):
                strategies.append(strategy_class())
                print(f"✓ {display_name}")
            else:
                print(f"⚠ {display_name} - one or both models not available")
        except Exception as e:
            print(f"⚠️  {display_name} skipped: {e}")

    print("=" * 60)

    if not strategies:
        print("\n❌ No strategies available!")
        print("💡 Single models: qwen3, minicpm")
        print("💡 Hybrid V2: hybrid-v2-qwen-first, hybrid-v2-minicpm-first")
        print("💡 Hybrid V3: hybrid-v3-qwen-first, hybrid-v3-minicpm-first")
        return 1

    # Find test images
    # Filter based on user options
    if hasattr(args, "difficult_only") and args.difficult_only:
        search_paths = [Path("barPictures/difficult")]
    else:
        # Start with difficult folder, then add sorted folder
        search_paths = [
            Path("barPictures/difficult"),
            Path("barPictures/Renamed-and-Sorted"),
        ]

    all_images = []
    for base_path in search_paths:
        if base_path.exists():
            all_images.extend(base_path.rglob("*.jpg"))
            all_images.extend(base_path.rglob("*.jpeg"))
            all_images.extend(base_path.rglob("*.png"))

    if not all_images:
        print("\n❌ No test images found!")
        return 1

    # Select images based on mode
    if args.quick:
        test_images = random.sample(all_images, min(3, len(all_images)))
        mode = "QUICK (3 random images)"
    else:
        test_images = all_images
        mode = f"FULL ({len(all_images)} images)"

    # Determine execution mode
    ollama_optimized = getattr(args, "ollama_optimized", False)
    if ollama_optimized:
        exec_mode = "OLLAMA-OPTIMIZED (models sequential, images parallel)"
    elif args.map_reduce:
        exec_mode = "MAP-REDUCE (strategies parallel)"
    else:
        exec_mode = "STANDARD"

    print("🔬 Starting strategy benchmark")
    print("=" * 60)
    print(f"Mode: {mode}")
    print(f"Execution: {exec_mode}")
    print(f"Strategies: {len(strategies)}")
    print(f"Images: {len(test_images)}")
    if not args.map_reduce and not ollama_optimized:
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

    # Choose execution mode
    if ollama_optimized:
        # Best for local Ollama models - avoids model switching
        comparator.test_multiple_images_ollama_optimized(image_cases)
    elif args.map_reduce:
        # Best for Cloud APIs (ChatGPT, Gemini)
        comparator.test_multiple_images_map_reduce(image_cases)
    else:
        comparator.test_multiple_images(image_cases)

    # Save results (JSON and CSV)
    output_file = Path("reports/strategy_benchmark_results.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    comparator.save_results(output_file)

    # Also save CSV for easy human review
    csv_file = output_file.with_suffix(".csv")
    comparator.save_results_csv(csv_file)

    print(f"📊 Results saved to: {output_file}")
    print(f"📊 CSV saved to: {csv_file}")
    print("\n💡 Generate report: python -m tools.cli.report")

    return 0
