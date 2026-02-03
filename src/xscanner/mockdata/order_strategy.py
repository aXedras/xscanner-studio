from __future__ import annotations

import json
import re
from pathlib import Path

from xscanner.server.order.strategy import OrderStrategyChoice

# Default fixtures per strategy.
#
# Rationale: In `use_mock=true` mode, clients should get a stable response even
# if no specific fixture exists for an upload filename. Specific fixtures remain
# a bonus.
#
# Note: today we point multiple strategies at the same default fixture. This is
# intentional and can be refined later by recording per-strategy defaults.
_DEFAULT_MOCK_NAME_BY_STRATEGY: dict[OrderStrategyChoice, str] = {
    OrderStrategyChoice.manual: "order_strategy_manual_72056547_pdf",
    OrderStrategyChoice.cloud: "order_strategy_manual_72056547_pdf",
    OrderStrategyChoice.local: "order_strategy_manual_72056547_pdf",
    OrderStrategyChoice.auto: "order_strategy_manual_72056547_pdf",
}


def get_default_order_strategy_mock_name(*, strategy: OrderStrategyChoice) -> str:
    name = _DEFAULT_MOCK_NAME_BY_STRATEGY.get(strategy)
    if not name:
        raise ValueError(f"No default order strategy mock configured for: {strategy.value}")
    return name


def _mock_dir() -> Path:
    # Keep recorded mocks inside the repo working tree.
    return Path(__file__).resolve().parent / "order_strategy"


_FILENAME_SAFE_RE = re.compile(r"[^a-z0-9_-]+")


def build_order_strategy_mock_name_from_upload_filename(
    *,
    strategy: OrderStrategyChoice,
    upload_filename: str | None,
) -> str:
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
    return f"order_strategy_{strategy.value}_{stem_slug or 'unnamed'}{ext_part}"


def get_order_strategy_mock_path(name: str) -> Path:
    safe = (name or "").strip()
    if not safe:
        raise ValueError("mock name must not be empty")
    return _mock_dir() / f"{safe}.json"


def read_order_strategy_mock_text(name: str) -> str | None:
    path = get_order_strategy_mock_path(name)
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8").strip() or None


def write_order_strategy_mock_text(*, name: str, text: str, overwrite: bool = False) -> Path:
    path = get_order_strategy_mock_path(name)
    if path.exists() and not overwrite:
        raise FileExistsError(f"Mock file already exists: {path}")

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
