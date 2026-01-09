"""Helper utilities for integration tests."""

import re
from pathlib import Path
from typing import Any

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png")
KNOWN_METALS = {"gold", "silver", "platinum", "palladium"}
OZT_TO_GRAMS = 31.1034768
PRIORITY_IMAGE_DIRS = [Path("barPictures") / "Renamed-and-Sorted Au, Ag, Pt"]


def is_image_file(path: Path) -> bool:
    """Check if path is an image file."""
    return path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS


def collect_image_paths() -> list[Path]:
    """Collect all test image paths, prioritizing specific directories."""
    images: list[Path] = []
    seen: set[str] = set()

    def add_candidate(candidate: Path) -> None:
        if not is_image_file(candidate):
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
                if is_image_file(path):
                    add_candidate(path)

        for path in sorted(bar_pics_dir.rglob("*")):
            if is_image_file(path):
                add_candidate(path)

    return images


def parse_weight_token(token: str) -> tuple[float | None, str | None]:
    """Parse weight value and unit from token."""
    if not token:
        return None, None
    match = re.match(r"(?P<value>\d+(?:[.,]\d+)?)(?P<unit>[a-zA-Z]+)?", token.strip())
    if not match:
        return None, None
    value = float(match.group("value").replace(",", "."))
    unit = (match.group("unit") or "g").lower()
    return value, unit


def convert_weight_to_grams(value: float | None, unit: str | None) -> float | None:
    """Convert weight to grams based on unit."""
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


def normalize_fineness_value(token: str) -> float | None:
    """Normalize fineness value to decimal (0.0-1.0)."""
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


def clean_producer_name(token: str) -> str | None:
    """Clean and normalize producer name."""
    if not token:
        return None
    cleaned = re.sub(r"[_-]+", " ", token).strip()
    cleaned = re.sub(r"(duplicate|copy)$", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned or None


def parse_expected_metadata(image_path: Path) -> dict[str, Any] | None:
    """Parse expected metadata from image filename."""
    stem = image_path.stem
    parts = stem.split("_")
    if len(parts) < 4:
        return None
    metal = parts[0].strip()
    if metal.lower() not in KNOWN_METALS:
        return None

    weight_value, weight_unit = parse_weight_token(parts[1].strip())
    fineness_value = normalize_fineness_value(parts[2].strip())
    serial_number = parts[3].strip() or None
    producer = clean_producer_name(" ".join(parts[4:]).strip()) if len(parts) > 4 else None

    fields: dict[str, Any] = {"Metal": metal.capitalize()}
    normalized: dict[str, Any] = {}

    if weight_value is not None:
        weight_display = f"{weight_value:.0f}" if weight_value.is_integer() else f"{weight_value}"
        fields["Weight"] = weight_display
        fields["WeightUnit"] = (weight_unit or "g").lower()
        normalized["weight_grams"] = convert_weight_to_grams(weight_value, weight_unit)
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
    """Get all test image cases with expected metadata."""
    cases: list[dict[str, Any]] = []
    for image_path in collect_image_paths():
        cases.append({"path": image_path, "expected": parse_expected_metadata(image_path)})
    return cases


def summarize_match_stats(test_results: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    """Summarize match statistics from test results."""
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
