"""Validation utilities for extracted data quality checks."""

import re
from pathlib import Path

# Metal symbol ↔ name mapping for flexible validation
METAL_ALIASES: dict[str, str] = {
    "AU": "Gold",
    "AG": "Silver",
    "PT": "Platinum",
    "PD": "Palladium",
}


def _normalize_metal(value: str) -> str:
    """Normalize metal value to common name (e.g. 'AU' → 'Gold')."""
    upper = value.strip().upper()
    return METAL_ALIASES.get(upper, value.strip().title())


def parse_filename_ground_truth(image_path: Path) -> dict[str, str] | None:
    """Parse ground truth data from structured filename.

    Expected format: Metal_WeightInGrams_Fineness_SerialNumber_Producer.jpg
    Example: Gold_00250g_9999_D12669_Degussa.jpg

    Returns:
        Dict with ground truth data or None if filename doesn't match pattern
    """
    filename = image_path.stem  # Remove .jpg extension

    # Pattern: Metal_Weight_Fineness_SerialNumber_Producer
    # Weight format: 00250g (grams with leading zeros)
    # Fineness format: 9999 (will be converted to 999.9)
    pattern = r"^([A-Za-z]+)_(\d+)g_(\d+)_([A-Za-z0-9]+)_(.+)$"
    match = re.match(pattern, filename)

    if not match:
        return None

    metal, weight, fineness, serial, producer = match.groups()

    # Convert fineness: 9999 -> 999.9
    if len(fineness) == 4:
        fineness = f"{fineness[:3]}.{fineness[3]}"

    # Remove leading zeros from weight
    weight = str(int(weight))

    return {
        "Metal": metal,
        "Weight": weight,
        "WeightUnit": "g",
        "Fineness": fineness,
        "SerialNumber": serial,
        "Producer": producer,
    }


def validate_extraction(extracted_data: dict, ground_truth: dict) -> tuple[list[str], list[str]]:
    """Validate extracted data against ground truth.

    Args:
        extracted_data: Data extracted by strategy
        ground_truth: Expected data from filename

    Returns:
        Tuple of (successes, errors) - lists of validation messages
    """
    successes = []
    errors = []

    # 1. Metal - match allowing symbol aliases (AU=Gold, AG=Silver, etc.)
    if "Metal" not in extracted_data:
        errors.append("❌ Metal field missing")
    elif _normalize_metal(extracted_data["Metal"]) != _normalize_metal(ground_truth["Metal"]):
        errors.append(
            f"❌ Metal: expected '{ground_truth['Metal']}', got '{extracted_data['Metal']}'"
        )
    else:
        successes.append(f"✓ Metal: {extracted_data['Metal']}")

    # 2. Weight - must match (strip units if present)
    if "Weight" not in extracted_data:
        errors.append("❌ Weight field missing")
    else:
        extracted_weight = (
            str(extracted_data["Weight"]).replace("g", "").replace(".", "").replace(",", "").strip()
        )
        expected_weight = str(ground_truth["Weight"])
        if extracted_weight != expected_weight:
            errors.append(
                f"❌ Weight: expected '{expected_weight}g', got '{extracted_data['Weight']}'"
            )
        else:
            successes.append(f"✓ Weight: {extracted_data['Weight']}")

    # 3. Fineness - must match (allow formatting: 9999 = 999.9)
    if "Fineness" not in extracted_data:
        errors.append("❌ Fineness field missing")
    else:
        extracted_fineness = str(extracted_data["Fineness"]).replace(".", "").strip()
        expected_fineness = str(ground_truth["Fineness"]).replace(".", "").strip()
        if extracted_fineness != expected_fineness:
            errors.append(
                f"❌ Fineness: expected '{ground_truth['Fineness']}', got '{extracted_data['Fineness']}'"
            )
        else:
            successes.append(f"✓ Fineness: {extracted_data['Fineness']}")

    # 4. Producer - must match exactly
    if "Producer" not in extracted_data:
        errors.append("❌ Producer field missing")
    elif extracted_data["Producer"] != ground_truth["Producer"]:
        errors.append(
            f"❌ Producer: expected '{ground_truth['Producer']}', got '{extracted_data['Producer']}'"
        )
    else:
        successes.append(f"✓ Producer: {extracted_data['Producer']}")

    # 5. SerialNumber - must match exactly
    if "SerialNumber" not in extracted_data:
        errors.append("❌ SerialNumber field missing")
    elif extracted_data["SerialNumber"] != ground_truth["SerialNumber"]:
        errors.append(
            f"❌ SerialNumber: expected '{ground_truth['SerialNumber']}', got '{extracted_data['SerialNumber']}'"
        )
    else:
        successes.append(f"✓ SerialNumber: {extracted_data['SerialNumber']}")

    return successes, errors
