from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _mock_dir() -> Path:
    # Keep recorded mocks inside the repo working tree.
    return Path(__file__).resolve().parent / "order_vision"


_FILENAME_SAFE_RE = re.compile(r"[^a-z0-9_-]+")


def build_order_vision_mock_name_from_upload_filename(*, upload_filename: str | None) -> str:
    """Build a deterministic mock fixture name from an upload filename.

    This MUST match the filename sent by the client.
    """

    raw = (upload_filename or "").strip()
    base = Path(raw).name

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

    if len(stem_slug) > 80:
        stem_slug = stem_slug[:80].rstrip("-_")

    ext_part = f"_{suffix_slug}" if suffix_slug else ""
    return f"order_vision_{stem_slug or 'unnamed'}{ext_part}"


def get_order_vision_mock_path(name: str) -> Path:
    safe = (name or "").strip()
    if not safe:
        raise ValueError("mock name must not be empty")
    return _mock_dir() / f"{safe}.json"


def read_order_vision_mock(name: str) -> dict[str, Any] | None:
    path = get_order_vision_mock_path(name)
    if not path.exists():
        return None
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return None
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("Recorded vision mock must be a JSON object")
    return parsed


def write_order_vision_mock(
    *,
    name: str,
    marker_text: str,
    provider: str,
    model: str,
    usage: dict[str, Any] | None,
    overwrite: bool = False,
    meta: dict[str, Any] | None = None,
) -> Path:
    path = get_order_vision_mock_path(name)
    if path.exists() and not overwrite:
        raise FileExistsError(f"Mock file already exists: {path}")

    marker_text = (marker_text or "").strip()
    if not marker_text:
        raise ValueError("marker_text must not be empty")

    payload: dict[str, Any] = {
        "marker_text": marker_text,
        "provider": str(provider or ""),
        "model": str(model or ""),
        "usage": usage or {},
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "meta": meta or {},
    }

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
