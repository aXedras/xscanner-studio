from __future__ import annotations

import json
import re
from pathlib import Path


def _mock_dir() -> Path:
    # Keep recorded mocks inside the repo working tree.
    return Path(__file__).resolve().parent / "order_extract"


_FILENAME_SAFE_RE = re.compile(r"[^a-z0-9_-]+")


def build_order_extract_mock_name_from_upload_filename(*, upload_filename: str | None) -> str:
    """Build a deterministic mock fixture name from an upload filename.

    Rationale: we want `use_mock=true` without any extra API parameters.
    The server derives the fixture name from the uploaded filename.
    This works across PDFs and images (e.g. .jpg) and avoids hashing bytes.

    Important: this MUST match the filename sent by the client.
    """

    raw = (upload_filename or "").strip()
    base = Path(raw).name  # drop any path segments for safety

    # Split into stem + suffix. We keep the suffix (extension) because it will
    # matter once we support images.
    p = Path(base)
    stem = (p.stem or "").strip().lower()
    suffix = (p.suffix or "").lstrip(".").strip().lower()

    def _slug(part: str) -> str:
        part = part.replace(" ", "-")
        part = _FILENAME_SAFE_RE.sub("-", part)
        part = part.strip("-_")
        return part

    stem_slug = _slug(stem)
    suffix_slug = _slug(suffix)

    if not stem_slug and not suffix_slug:
        raise ValueError("upload filename must not be empty")

    # Keep names short-ish and predictable for fixture files.
    if len(stem_slug) > 80:
        stem_slug = stem_slug[:80].rstrip("-_")

    ext_part = f"_{suffix_slug}" if suffix_slug else ""
    return f"order_extract_{stem_slug or 'unnamed'}{ext_part}"


def get_order_extract_mock_path(name: str) -> Path:
    safe = (name or "").strip()
    if not safe:
        raise ValueError("mock name must not be empty")
    return _mock_dir() / f"{safe}.json"


def read_order_extract_mock_text(name: str) -> str | None:
    path = get_order_extract_mock_path(name)
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8").strip() or None


def write_order_extract_mock_text(*, name: str, text: str, overwrite: bool = False) -> Path:
    path = get_order_extract_mock_path(name)
    if path.exists() and not overwrite:
        raise FileExistsError(f"Mock file already exists: {path}")

    # Validate that it is JSON and looks like the expected envelope.
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError("Recorded mock must be a JSON object")

    expected_keys = {"meta", "raw", "structured_data"}
    if set(parsed.keys()) != expected_keys:
        raise ValueError(
            f"Recorded mock must have exactly the keys {sorted(expected_keys)}; got {sorted(parsed.keys())}"
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(parsed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
