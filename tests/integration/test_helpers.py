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

    Uses committed test images under `tests/fixtures/images/bars`.
    Tests must fail loudly if the fixtures are missing.
    """
    repo_root = Path(__file__).resolve().parents[2]

    committed_dir = repo_root / "tests" / "fixtures" / "images" / "bars"
    if not committed_dir.exists():
        raise RuntimeError(
            f"Committed test images directory not found: {committed_dir}. "
            "Expected 3 bar images to be checked in under tests/fixtures/images/bars/."
        )

    images: list[Path] = []
    for image_path in sorted(committed_dir.glob("*.jpg")):
        if is_image_file(image_path) and parse_filename_ground_truth(image_path):
            images.append(image_path)

    if not images:
        raise RuntimeError(
            f"No valid test images found in {committed_dir}. "
            "Expected .jpg files with parseable ground truth in the filename."
        )

    return images


def get_random_test_image() -> Path | None:
    """Get a random test image with ground truth data."""
    images = collect_image_paths()
    if not images:
        return None
    return random.choice(images)
