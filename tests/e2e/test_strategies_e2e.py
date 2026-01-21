"""End-to-end tests for all extraction strategies.

These tests make real API/service calls and validate extracted data
against ground truth from structured filenames.

Required configuration:
- ChatGPT: OPENAI_API_KEY
- Gemini: GOOGLE_API_KEY
- Hybrid: Ollama service running locally
"""

import pytest
from test_helpers import get_random_test_image

from tools.cli.validator import parse_filename_ground_truth, validate_extraction
from xscanner.server.config import get_config
from xscanner.strategy.chatgpt_vision_strategy import ChatGPTVisionStrategy
from xscanner.strategy.gemini_flash_strategy import GeminiFlashStrategy

# Check if PaddleOCR is available for hybrid strategy
try:
    from xscanner.strategy.paddle_ollama_hybrid_strategy import PaddleLlamaHybridStrategy

    PADDLE_AVAILABLE = True
except ImportError:
    PADDLE_AVAILABLE = False

pytestmark = pytest.mark.e2e


@pytest.fixture(scope="module")
def config():
    """Load application configuration."""
    return get_config()


@pytest.fixture(scope="module")
def test_image_with_ground_truth():
    """Get a random test image with ground truth data from filename."""
    image_path = get_random_test_image()
    if not image_path:
        pytest.skip("No test images with ground truth found")

    ground_truth = parse_filename_ground_truth(image_path)
    if not ground_truth:
        pytest.skip(f"Could not parse ground truth from {image_path.name}")

    return image_path, ground_truth


@pytest.fixture(scope="module")
def chatgpt_strategy(config):
    """Create ChatGPT strategy if API key is configured."""
    if not config.openai.api_key:
        pytest.skip("OPENAI_API_KEY not configured")
    return ChatGPTVisionStrategy(
        api_key=config.openai.api_key,
        model=config.openai.model,
        temperature=config.openai.temperature,
        max_output_tokens=config.openai.max_output_tokens,
    )


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
def hybrid_strategy(config):
    """Create Hybrid strategy if Ollama is running."""
    if not PADDLE_AVAILABLE:
        pytest.skip("PaddleOCR not installed")

    if not config.ollama.base_url:
        pytest.skip("Ollama base URL not configured")

    try:
        # Test if Ollama is reachable
        import requests

        response = requests.get(f"{config.ollama.base_url}/api/tags", timeout=2)
        if response.status_code != 200:
            pytest.skip("Ollama service not responding")
    except Exception:
        pytest.skip("Ollama service not reachable")

    return PaddleLlamaHybridStrategy(base_url=config.ollama.base_url)


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


def test_gemini_e2e(gemini_strategy, test_image_with_ground_truth):
    """End-to-end test: Real Gemini API call validated against ground truth."""
    test_image, ground_truth = test_image_with_ground_truth
    result = gemini_strategy.extract(test_image)
    _validate_strategy_result("Gemini Flash", result, test_image, ground_truth)


def test_hybrid_e2e(hybrid_strategy, test_image_with_ground_truth):
    """End-to-end test: Real Hybrid strategy call validated against ground truth."""
    test_image, ground_truth = test_image_with_ground_truth
    result = hybrid_strategy.extract(test_image)
    _validate_strategy_result("Paddle+Llama Hybrid", result, test_image, ground_truth)
