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

# Map snake_case keys (from JSON schema) to PascalCase (ground truth convention)
_KEY_MAP: dict[str, str] = {
    "metal": "Metal",
    "weight": "Weight",
    "weight_unit": "WeightUnit",
    "fineness": "Fineness",
    "serial_number": "SerialNumber",
    "producer": "Producer",
    "category": "Category",
    "serial_number_visibility": "SerialNumberVisibility",
    "visible_damage": "VisibleDamage",
}


def _normalize_keys(data: dict) -> dict:
    """Normalize extraction keys to PascalCase for consistent validation.

    Strategies return snake_case keys (per JSON schema), ground truth
    uses PascalCase.  Accept both transparently.
    """
    return {_KEY_MAP.get(k, k): v for k, v in data.items()}


def _normalize_metal(value: str) -> str:
    """Normalize metal value to common name (e.g. 'AU' → 'Gold')."""
    upper = value.strip().upper()
    return METAL_ALIASES.get(upper, value.strip().title())


def _normalize_fineness(value) -> str:
    """Normalize fineness to integer-thousandths string for comparison.

    Handles both decimal format from API (0.9999) and
    human-readable format from ground truth (999.9 or 9999).

    Examples:
        0.9999  → "9999"
        0.999   → "9990"
        999.9   → "9999"
        9999    → "9999"
        "999.9" → "9999"
    """
    num = float(value)
    if num < 1:
        # Decimal format (0.9999) → multiply by 10000 and round
        return str(round(num * 10000))
    # Already in absolute format (999.9, 9999)
    return str(value).replace(".", "").strip()


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

    Handles both snake_case (from strategy JSON schema) and PascalCase keys
    transparently.

    Args:
        extracted_data: Data extracted by strategy
        ground_truth: Expected data from filename

    Returns:
        Tuple of (successes, errors) - lists of validation messages
    """
    successes = []
    errors = []

    # Normalize keys so both snake_case and PascalCase inputs work
    data = _normalize_keys(extracted_data)

    # 1. Metal - match allowing symbol aliases (AU=Gold, AG=Silver, etc.)
    if "Metal" not in data:
        errors.append("❌ Metal field missing")
    elif _normalize_metal(data["Metal"]) != _normalize_metal(ground_truth["Metal"]):
        errors.append(f"❌ Metal: expected '{ground_truth['Metal']}', got '{data['Metal']}'")
    else:
        successes.append(f"✓ Metal: {data['Metal']}")

    # 2. Weight - must match (strip units if present)
    if "Weight" not in data:
        errors.append("❌ Weight field missing")
    else:
        extracted_weight = (
            str(data["Weight"]).replace("g", "").replace(".", "").replace(",", "").strip()
        )
        expected_weight = str(ground_truth["Weight"])
        if extracted_weight != expected_weight:
            errors.append(f"❌ Weight: expected '{expected_weight}g', got '{data['Weight']}'")
        else:
            successes.append(f"✓ Weight: {data['Weight']}")

    # 3. Fineness - must match (allow formatting: 9999 = 999.9 = 0.9999)
    if "Fineness" not in data:
        errors.append("❌ Fineness field missing")
    else:
        extracted_fineness = _normalize_fineness(data["Fineness"])
        expected_fineness = _normalize_fineness(ground_truth["Fineness"])
        if extracted_fineness != expected_fineness:
            errors.append(
                f"❌ Fineness: expected '{ground_truth['Fineness']}', got '{data['Fineness']}'"
            )
        else:
            successes.append(f"✓ Fineness: {data['Fineness']}")

    # 4. Producer - must match exactly
    if "Producer" not in data:
        errors.append("❌ Producer field missing")
    elif data["Producer"] != ground_truth["Producer"]:
        errors.append(
            f"❌ Producer: expected '{ground_truth['Producer']}', got '{data['Producer']}'"
        )
    else:
        successes.append(f"✓ Producer: {data['Producer']}")

    # 5. SerialNumber - must match exactly
    if "SerialNumber" not in data:
        errors.append("❌ SerialNumber field missing")
    elif data["SerialNumber"] != ground_truth["SerialNumber"]:
        errors.append(
            f"❌ SerialNumber: expected '{ground_truth['SerialNumber']}', got '{data['SerialNumber']}'"
        )
    else:
        successes.append(f"✓ SerialNumber: {data['SerialNumber']}")

    return successes, errors
