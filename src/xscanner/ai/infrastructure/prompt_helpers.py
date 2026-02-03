from __future__ import annotations

import json
from pathlib import Path


def read_required_prompt_text(path: Path) -> str:
    """Read a prompt template file and ensure it is non-empty.

    This helper is intentionally generic and lives under xscanner.ai so it can be
    reused by multiple domains (e.g. order, extraction) that load prompt templates
    from the repo config directory.

    Raises:
        ValueError: If the file is empty after stripping whitespace.
        OSError: If the file cannot be read.
    """

    content = path.read_text(encoding="utf-8").strip()
    if not content:
        raise ValueError(f"Required prompt file is empty: {path}")
    return content


def read_required_json_object(path: Path) -> dict:
    """Read a required JSON config file and ensure it contains a JSON object.

    This is intentionally generic and can be reused across domains.

    Raises:
        ValueError: If the file cannot be parsed or is not a JSON object.
        OSError: If the file cannot be read.
    """

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"Failed to parse required JSON config file: {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in config file: {path}")

    return data
