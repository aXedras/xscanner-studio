"""End-to-end tests for all extraction strategies.

These tests make real API/service calls and validate extracted data
against ground truth from structured filenames.

Required configuration:
- ChatGPT: OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE
- Gemini: GOOGLE_API_KEY
- Local: LoRA fine-tuned service reachable via LORA_BASE_URL
"""

import os
from pathlib import Path

import pytest

from tools.cli.validator import parse_filename_ground_truth, validate_extraction
from xscanner.server.config import get_config
from xscanner.strategy.chatgpt_vision_strategy import ChatGPTVisionStrategy
from xscanner.strategy.gemini_flash_strategy import GeminiFlashStrategy
from xscanner.strategy.lora_finetuned_strategy import LoRAFinetunedStrategy

pytestmark = pytest.mark.e2e


@pytest.fixture(scope="module")
def config():
    """Load application configuration."""
    return get_config()


@pytest.fixture(scope="module")
def test_image_with_ground_truth():
    """Get a committed test image with filename-based ground truth.

    This is intentionally deterministic so CI runs are reproducible.
    """

    tests_dir = Path(__file__).resolve().parents[1]
    images_dir = tests_dir / "fixtures" / "images" / "bars"
    paths = sorted(images_dir.glob("*.jpg"))
    if len(paths) != 3:
        raise RuntimeError(
            f"Expected exactly 3 committed test images in {images_dir}, found {len(paths)}"
        )

    preferred_order = [
        "Gold_00500g_9999_A55251_Heraeus.jpg",
        "Gold_00500g_9999_D08744_Degussa.jpg",
        "Gold_00100g_9999_614938_Credit Suisse.jpg",
    ]

    by_name = {p.name: p for p in paths}
    image_path = next((by_name[name] for name in preferred_order if name in by_name), paths[0])
    ground_truth = parse_filename_ground_truth(image_path)
    if not ground_truth:
        raise RuntimeError(f"Could not parse ground truth from {image_path.name}")

    return image_path, ground_truth


@pytest.fixture(scope="module")
def chatgpt_strategy():
    """Create ChatGPT strategy if env vars are configured."""
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not configured")
    if not os.environ.get("OPENAI_MODEL"):
        pytest.skip("OPENAI_MODEL not configured")
    if not os.environ.get("OPENAI_TEMPERATURE"):
        pytest.skip("OPENAI_TEMPERATURE not configured")
    return ChatGPTVisionStrategy()


@pytest.fixture(scope="module")
def gemini_strategy(config):
    """Create Gemini strategy if API key is configured."""
    if not config.google.api_key:
        pytest.skip("GOOGLE_API_KEY not configured")
    return GeminiFlashStrategy(
        api_key=config.google.api_key,
        model=config.google.model,
    )


@pytest.fixture(scope="module")
def lora_strategy(config):
    """Create LoRA strategy if local LoRA service is running."""
    if not config.lora.base_url:
        pytest.skip("LORA_BASE_URL not configured")

    if not LoRAFinetunedStrategy.is_available(config.lora.base_url):
        pytest.skip("LoRA service not reachable")

    return LoRAFinetunedStrategy(base_url=config.lora.base_url)


def _validate_strategy_result(strategy_name: str, result, test_image, ground_truth):
    """Common validation logic for all strategies.

    Args:
        strategy_name: Display name of the strategy
        result: ExtractionResult from strategy
        test_image: Path to test image
        ground_truth: Expected values from filename

    Raises:
        pytest.fail if validation fails
    """
    print(f"\n{'=' * 80}")
    print(f"Testing: {strategy_name}")
    print(f"{'=' * 80}")
    print(f"📸 Image: {test_image.name}")
    print(f"📂 Path: {test_image}")
    print(f"🎯 Ground Truth: {ground_truth}")
    print(f"✓ Image exists: {test_image.exists()}")

    # Verify result structure
    assert result is not None, "Strategy should return a result"
    assert result.processing_time > 0, "Processing time should be positive"
    assert isinstance(result.structured_data, dict), "Structured data should be a dictionary"

    # Log raw output for debugging CI failures
    print(f"📝 Raw output: {result.raw_text[:500] if result.raw_text else 'None'}...")
    if result.error:
        print(f"⚠️  Error: {result.error}")

    data = result.structured_data
    print(f"🤖 Extracted: {data}")
    print(f"📊 Confidence: {result.confidence}")
    print(f"⏱️  Processing time: {result.processing_time:.2f}s")

    # Validate against ground truth
    successes, errors = validate_extraction(data, ground_truth)

    # Print successes
    if successes:
        print("\n✅ Successful validations:")
        for success in successes:
            print(f"  {success}")

    # Print errors and fail if any
    if errors:
        print(f"\n❌ Validation Errors ({len(errors)}):")
        for error in errors:
            print(f"  {error}")
        pytest.fail(f"Validation failed with {len(errors)} error(s): {'; '.join(errors)}")
    else:
        print("\n✅ All validations passed!")
        print(f"Processing time: {result.processing_time:.2f}s")


def test_chatgpt_e2e(chatgpt_strategy, test_image_with_ground_truth):
    """End-to-end test: Real ChatGPT API call validated against ground truth."""
    test_image, ground_truth = test_image_with_ground_truth
    result = chatgpt_strategy.extract(test_image)
    _validate_strategy_result("ChatGPT Vision", result, test_image, ground_truth)


def test_lora_e2e(lora_strategy, test_image_with_ground_truth):
    """End-to-end test: Real LoRA server call validated against ground truth."""
    test_image, ground_truth = test_image_with_ground_truth
    result = lora_strategy.extract(test_image)
    _validate_strategy_result("LoRA Fine-tuned", result, test_image, ground_truth)


@pytest.mark.skip(reason="No budget for Gemini API calls")
def test_gemini_e2e(gemini_strategy, test_image_with_ground_truth):
    """End-to-end test: Real Gemini API call validated against ground truth."""
    test_image, ground_truth = test_image_with_ground_truth
    result = gemini_strategy.extract(test_image)
    _validate_strategy_result("Gemini Flash", result, test_image, ground_truth)
