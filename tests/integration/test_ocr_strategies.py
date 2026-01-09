#!/usr/bin/env python3
"""
Integration tests for OCR strategies - requires API keys and external services.

Mark tests with @pytest.mark.integration to skip during fast unit test runs.
"""

import os
import re
import sys
from pathlib import Path
from typing import Any

import pytest

# Lazy imports to avoid loading all dependencies at once
from xscanner.benchmark.comparator import OCRComparator
from xscanner.server.config import get_config

pytestmark = pytest.mark.integration  # Mark all tests in this module as integration

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png")
KNOWN_METALS = {"gold", "silver", "platinum", "palladium"}
OZT_TO_GRAMS = 31.1034768
PRIORITY_IMAGE_DIRS = [Path("barPictures") / "Renamed-and-Sorted Au, Ag, Pt"]


def _is_image_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS


def _collect_image_paths() -> list[Path]:
    images: list[Path] = []
    seen: set[str] = set()

    def add_candidate(candidate: Path) -> None:
        if not _is_image_file(candidate):
            return
        key = str(candidate.resolve())
        if key in seen:
            return
        seen.add(key)
        images.append(candidate)

    bild_path = Path("Bild.jpeg")
    if bild_path.exists():
        add_candidate(bild_path)

    bar_pics_dir = Path("barPictures")
    if bar_pics_dir.exists():
        priority_dirs = [p for p in PRIORITY_IMAGE_DIRS if p.exists()]
        for root in priority_dirs:
            for path in sorted(root.rglob("*")):
                if _is_image_file(path):
                    add_candidate(path)

        for path in sorted(bar_pics_dir.rglob("*")):
            if _is_image_file(path):
                add_candidate(path)

    return images


def _parse_weight_token(token: str) -> tuple[float | None, str | None]:
    if not token:
        return None, None
    match = re.match(r"(?P<value>\d+(?:[.,]\d+)?)(?P<unit>[a-zA-Z]+)?", token.strip())
    if not match:
        return None, None
    value = float(match.group("value").replace(",", "."))
    unit = (match.group("unit") or "g").lower()
    return value, unit


def _convert_weight_to_grams(value: float | None, unit: str | None) -> float | None:
    if value is None:
        return None
    unit_norm = (unit or "g").lower()
    if unit_norm in {"g", "gram", "grams"}:
        return value
    if unit_norm in {"kg", "kilogram", "kilograms"}:
        return value * 1000
    if unit_norm in {"oz", "ounce", "ozt", "troyounce"}:
        return value * OZT_TO_GRAMS
    return value


def _normalize_fineness_value(token: str) -> float | None:
    if not token:
        return None
    cleaned = re.sub(r"[^0-9.,]", "", token).replace(",", ".").strip()
    if not cleaned:
        return None
    try:
        value = float(cleaned)
    except ValueError:
        return None
    while value > 2:
        value /= 10
    return value if value > 0 else None


def _clean_producer_name(token: str) -> str | None:
    if not token:
        return None
    cleaned = re.sub(r"[_-]+", " ", token).strip()
    cleaned = re.sub(r"(duplicate|copy)$", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned or None


def parse_expected_metadata(image_path: Path) -> dict[str, Any] | None:
    stem = image_path.stem
    parts = stem.split("_")
    if len(parts) < 4:
        return None
    metal = parts[0].strip()
    if metal.lower() not in KNOWN_METALS:
        return None

    weight_value, weight_unit = _parse_weight_token(parts[1].strip())
    fineness_value = _normalize_fineness_value(parts[2].strip())
    serial_number = parts[3].strip() or None
    producer = _clean_producer_name(" ".join(parts[4:]).strip()) if len(parts) > 4 else None

    fields: dict[str, Any] = {"Metal": metal.capitalize()}
    normalized: dict[str, Any] = {}

    if weight_value is not None:
        weight_display = f"{weight_value:.0f}" if weight_value.is_integer() else f"{weight_value}"
        fields["Weight"] = weight_display
        fields["WeightUnit"] = (weight_unit or "g").lower()
        normalized["weight_grams"] = _convert_weight_to_grams(weight_value, weight_unit)
    if fineness_value is not None:
        fields["Fineness"] = f"{fineness_value:.4f}".rstrip("0").rstrip(".")
        normalized["fineness_decimal"] = fineness_value
    if serial_number:
        fields["SerialNumber"] = serial_number
    if producer:
        fields["Producer"] = producer

    # Remove empty entries
    fields = {k: v for k, v in fields.items() if v}

    if not fields:
        return None

    normalized = {k: v for k, v in normalized.items() if v is not None}

    return {
        "source": "filename",
        "fields": fields,
        "normalized": normalized,
    }


def get_test_image_cases() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for image_path in _collect_image_paths():
        cases.append({"path": image_path, "expected": parse_expected_metadata(image_path)})
    return cases


def _summarize_match_stats(test_results: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    summary: dict[str, dict[str, float]] = {}
    for test in test_results:
        for strategy_name, result in test.get("results", {}).items():
            comparison = result.get("comparison")
            if not comparison:
                continue
            stats = summary.setdefault(
                strategy_name,
                {
                    "images_with_truth": 0,
                    "perfect_matches": 0,
                    "matched_fields": 0,
                    "total_fields": 0,
                },
            )
            stats["images_with_truth"] += 1 if comparison.get("total_expected_fields") else 0
            stats["matched_fields"] += comparison.get("matched_fields", 0) or 0
            stats["total_fields"] += comparison.get("total_expected_fields", 0) or 0
            if comparison.get("pass"):
                stats["perfect_matches"] += 1
    return summary


def make_strategy_factory(module_path: str, class_name: str, *args, **kwargs):
    """Create a lazy factory that imports the strategy only when invoked."""

    def _factory():
        module = __import__(module_path, fromlist=[class_name])
        strategy_cls = getattr(module, class_name)
        return strategy_cls(*args, **kwargs)

    return _factory


def main():
    """Main execution"""
    print("=" * 80)
    print("OCR STRATEGY COMPARISON TEST")
    print("=" * 80)

    # Load configuration from .env.local
    print("\nLoading configuration from .env.local...")
    try:
        config = get_config()
        openai_key = config.openai.api_key
        openai_model = config.openai.model
        openai_temp = config.openai.temperature
        openai_max_tokens = config.openai.max_output_tokens

        if openai_key:
            print("✓ OpenAI key loaded")
        else:
            print("⚠ OpenAI key not set")

        gemini_key = config.google.api_key
        if gemini_key:
            print("✓ Google API key loaded")
        else:
            print("⚠ Google API key not set")

        deepseek_key = config.deepseek.api_key
        if deepseek_key:
            print("✓ DeepSeek API key loaded")
        else:
            print("⚠ DeepSeek API key not set")

    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        print("Make sure .env.local exists with your API keys")
        sys.exit(1)

    # Initialize strategies with lazy imports
    print("\nInitializing OCR strategies...")
    strategies = []

    strategy_specs = []

    def add_strategy(label: str, factory, enabled: bool = True, skip_reason: str | None = None):
        strategy_specs.append(
            {"label": label, "factory": factory, "enabled": enabled, "skip_reason": skip_reason}
        )

    # Tesseract removed - lowest accuracy among OCR strategies
    # EasyOCR removed - hangs forever, unreliable timeouts
    add_strategy(
        "PaddleOCR (may take time on first run)",
        make_strategy_factory("ocr_strategies.paddleocr_strategy", "PaddleOCRStrategy"),
    )
    # Regex/NLP removed - insufficient accuracy, relies on OCR output that's often incomplete
    # YOLOv8 removed - insufficient accuracy for bullion bar recognition
    # Only using Gemini Flash 2.0, not Gemini Vision (to avoid duplication)
    add_strategy(
        "Gemini Flash 2.0",
        make_strategy_factory(
            "ocr_strategies.gemini_flash_strategy",
            "GeminiFlashStrategy",
            api_key=gemini_key,
            model="gemini-2.0-flash",
        ),
        enabled=bool(gemini_key),
        skip_reason="no GOOGLE_API_KEY",
    )
    # =========================================================================
    # OLLAMA HYBRID STRATEGY - Runs PaddleOCR + Llama 11B in parallel (max_workers=2)
    # Moderate parallelization, should not cause resource issues
    # =========================================================================
    add_strategy(
        "Hybrid: PaddleOCR + Llama 11B (parallel)",
        make_strategy_factory(
            "ocr_strategies.paddle_llama_hybrid_strategy", "PaddleLlamaHybridStrategy"
        ),
    )
    # Other Ollama strategies disabled for this test run
    add_strategy(
        f"ChatGPT Vision ({openai_model})",
        make_strategy_factory(
            "ocr_strategies.chatgpt_vision_strategy",
            "ChatGPTVisionStrategy",
            api_key=openai_key,
            model=openai_model,
            temperature=openai_temp,
            max_output_tokens=openai_max_tokens,
        ),
        enabled=bool(openai_key),
        skip_reason="no API key",
    )
    # DeepSeek OCR removed - does not parse structured data correctly

    total_strategies = len(strategy_specs)
    for idx, spec in enumerate(strategy_specs, start=1):
        print(f"  [{idx}/{total_strategies}] {spec['label']}...", end=" ", flush=True)
        if not spec["enabled"]:
            reason = spec["skip_reason"] or "disabled"
            print(f"❌ Skipped ({reason})")
            continue
        try:
            strategies.append(spec["factory"]())
            print("✓")
        except Exception as e:
            print(f"❌ Skipped: {e}")

    print(f"\n✓ Initialized {len(strategies)} strategies total")
    try:
        strategy_workers = int(os.getenv("OCR_STRATEGY_WORKERS", "1"))
    except ValueError:
        strategy_workers = 1
    strategy_workers = max(1, strategy_workers)
    print(f"Strategy worker pool size: {strategy_workers}")

    # Get test images
    print("\nFinding test images...")
    image_cases = get_test_image_cases()

    if not image_cases:
        print("❌ No test images found!")
        print("   Expected: Bild.jpeg and/or images in barPictures/")
        sys.exit(1)

    limit_env = os.getenv("MAX_TEST_IMAGES")
    offset_env = os.getenv("IMAGE_OFFSET", "0")

    if limit_env:
        try:
            max_cases = int(limit_env)
        except ValueError:
            max_cases = None
        try:
            offset = int(offset_env)
        except ValueError:
            offset = 0

        if max_cases and max_cases > 0:
            original_len = len(image_cases)
            # Apply offset first, then limit
            image_cases = image_cases[offset : offset + max_cases]
            print(
                f"Limiting test run to images {offset} to {offset + len(image_cases)} "
                f"(requested {max_cases}, offset {offset}, total {original_len})"
            )
    else:
        # Default: run on half of images for faster testing
        original_len = len(image_cases)
        half_count = original_len // 2
        image_cases = image_cases[:half_count]
        print(f"Running on first half of images: {len(image_cases)} of {original_len} total")

    expected_count = sum(1 for case in image_cases if case.get("expected"))
    print(f"✓ Found {len(image_cases)} test images ({expected_count} with filename metadata):")
    for case in image_cases:
        status = "expected metadata" if case.get("expected") else "no metadata"
        print(f"   - {case['path']} [{status}]")

    # Run comparison
    print("\nStarting OCR comparison tests...")
    comparator = OCRComparator(strategies, max_workers=strategy_workers)
    _ = comparator.test_multiple_images(image_cases)

    # Print comparison
    comparator.print_comparison()

    # Show best strategy
    print(f"\n{'=' * 80}")
    print(f"Best Strategy: {comparator.get_best_strategy()}")
    print(f"{'=' * 80}")

    # Save results
    output_path = Path("ocr_comparison_results.json")
    comparator.save_results(output_path)

    match_summary = _summarize_match_stats(comparator.results)
    if match_summary:
        print("\nGround truth match summary:")
        for strategy_name, stats in sorted(match_summary.items()):
            total_fields = stats["total_fields"] or 1
            field_pct = (stats["matched_fields"] / total_fields) * 100
            print(
                f"  - {strategy_name}: {int(stats['perfect_matches'])}/"
                f"{int(stats['images_with_truth'])} perfect images, "
                f"{int(stats['matched_fields'])}/{int(stats['total_fields'])} fields ({field_pct:.1f}%)"
            )

    print("\n✓ Test completed successfully!")


if __name__ == "__main__":
    main()
