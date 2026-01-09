"""Helper utilities for integration and e2e tests."""

import random
import re
from pathlib import Path

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png")


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


def is_image_file(path: Path) -> bool:
    """Check if path is an image file."""
    return path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS


def collect_image_paths() -> list[Path]:
    """Collect test image paths from structured directory with ground truth.

    Only returns images from 'Renamed-and-Sorted Au, Ag, Pt' directory
    where filenames contain ground truth data.
    """
    images: list[Path] = []

    # Only use structured directory with ground truth in filenames
    structured_dir = Path("barPictures") / "Renamed-and-Sorted Au, Ag, Pt"
    if not structured_dir.exists():
        return images

    # Collect all images with parseable filenames
    for image_path in sorted(structured_dir.rglob("*.jpg")):
        if is_image_file(image_path) and parse_filename_ground_truth(image_path):
            images.append(image_path)

    return images


def get_random_test_image() -> Path | None:
    """Get a random test image with ground truth data."""
    images = collect_image_paths()
    if not images:
        return None
    return random.choice(images)
