"""Helper utilities for integration and e2e tests."""

import random
from pathlib import Path

from tools.cli.validator import parse_filename_ground_truth

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png")


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
