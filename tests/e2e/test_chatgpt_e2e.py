"""End-to-end test for extraction strategies.

This test makes a real API call to ChatGPT Vision API and validates
the extracted data against ground truth from structured filenames.
It requires OPENAI_API_KEY to be configured.
"""

import pytest
from test_helpers import get_random_test_image, parse_filename_ground_truth

from xscanner.server.config import get_config
from xscanner.strategy.chatgpt_vision_strategy import ChatGPTVisionStrategy

pytestmark = pytest.mark.e2e


@pytest.fixture(scope="module")
def config():
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
    if not config.openai.api_key:
        pytest.skip("OPENAI_API_KEY not configured")
    return ChatGPTVisionStrategy(
        api_key=config.openai.api_key,
        model=config.openai.model,
        temperature=config.openai.temperature,
        max_output_tokens=config.openai.max_output_tokens,
    )


def test_chatgpt_e2e(chatgpt_strategy, test_image_with_ground_truth):
    """End-to-end test: Real ChatGPT API call validated against ground truth."""
    test_image, ground_truth = test_image_with_ground_truth

    print(f"\n📸 Testing image: {test_image.name}")
    print(f"🎯 Ground Truth: {ground_truth}")

    # Execute extraction
    result = chatgpt_strategy.extract(test_image)

    # Verify result structure
    assert result is not None, "Strategy should return a result"
    assert result.processing_time > 0, "Processing time should be positive"
    assert result.strategy_name.startswith("ChatGPT Vision"), "Strategy name should match"
    assert isinstance(result.structured_data, dict), "Structured data should be a dictionary"

    data = result.structured_data
    print(f"🤖 Extracted: {data}")

    # CRITICAL: Validate extracted data against ground truth
    errors = []

    # 1. Metal must match exactly
    if "Metal" in data:
        if data["Metal"] != ground_truth["Metal"]:
            errors.append(
                f"Metal mismatch: expected '{ground_truth['Metal']}', got '{data['Metal']}'"
            )
    else:
        errors.append("Metal field missing in extracted data")

    # 2. Weight must match (allow unit conversion: kg -> g)
    if "Weight" in data:
        extracted_weight = str(data["Weight"]).replace(".", "").replace(",", "").strip()
        expected_weight = str(ground_truth["Weight"])

        # Handle unit conversion: if extracted is kg, convert to grams
        extracted_unit = data.get("WeightUnit", "g").lower()
        if extracted_unit == "kg":
            try:
                weight_in_grams = str(int(float(data["Weight"]) * 1000))
                if weight_in_grams != expected_weight:
                    errors.append(
                        f"Weight mismatch: expected '{expected_weight}g', got '{data['Weight']}kg' (={weight_in_grams}g)"
                    )
            except (ValueError, TypeError):
                errors.append(f"Weight conversion failed: '{data['Weight']}' {extracted_unit}")
        elif extracted_weight != expected_weight:
            errors.append(f"Weight mismatch: expected '{expected_weight}', got '{data['Weight']}'")
    else:
        errors.append("Weight field missing in extracted data")

    # 3. Fineness must match (allow minor formatting differences)
    if "Fineness" in data:
        extracted_fineness = str(data["Fineness"]).replace(",", ".").strip()
        expected_fineness = ground_truth["Fineness"]
        if extracted_fineness != expected_fineness:
            errors.append(
                f"Fineness mismatch: expected '{expected_fineness}', got '{data['Fineness']}'"
            )
    else:
        errors.append("Fineness field missing in extracted data")

    # 4. SerialNumber must match (case-insensitive)
    if "SerialNumber" in data:
        extracted_serial = str(data["SerialNumber"]).upper().strip()
        expected_serial = ground_truth["SerialNumber"].upper()
        if extracted_serial != expected_serial:
            errors.append(
                f"SerialNumber mismatch: expected '{ground_truth['SerialNumber']}', got '{data['SerialNumber']}'"
            )
    else:
        errors.append("SerialNumber field missing in extracted data")

    # 5. Producer must contain expected name (allow variations and expansions)
    if "Producer" in data:
        extracted_producer = data["Producer"].lower().replace("-", " ").replace("_", " ")
        expected_producer = ground_truth["Producer"].lower().replace("-", " ").replace("_", " ")
        # Allow both directions: expected in extracted OR extracted in expected
        # Also check for common abbreviations (CS = Credit Suisse)
        producer_aliases = {
            "cs": "credit suisse",
            "ah": "argor heraeus",
        }
        expected_full = producer_aliases.get(expected_producer, expected_producer)
        extracted_full = producer_aliases.get(extracted_producer, extracted_producer)

        if not (
            expected_producer in extracted_producer
            or extracted_producer in expected_producer
            or expected_full in extracted_producer
            or extracted_full in expected_producer
        ):
            errors.append(
                f"Producer mismatch: expected '{ground_truth['Producer']}', got '{data['Producer']}'"
            )
    else:
        errors.append("Producer field missing in extracted data")

    # Report results
    if errors:
        print(f"\n❌ Validation errors ({len(errors)}):")
        for error in errors:
            print(f"  - {error}")
        pytest.fail(
            f"Ground truth validation failed with {len(errors)} errors:\n" + "\n".join(errors)
        )
    else:
        print("\n✅ E2E Test successful! All fields match ground truth.")
        print(f"Processing time: {result.processing_time:.2f}s")
