from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from xscanner.ai.infrastructure import read_required_json_object

WhitelistHint = tuple[str, str, str | None]


@dataclass(frozen=True)
class Whitelist:
    values: list[str]
    aliases: dict[str, str]


def load_whitelist(*, file_name: str, base_dir: Path | None = None) -> Whitelist:
    base = base_dir or Path("config/whitelists")
    data = read_required_json_object(base / file_name)

    values_any = data.get("values")
    patterns_any = data.get("patterns")
    aliases_any = data.get("aliases")

    values: list[str]
    if isinstance(values_any, list) and all(isinstance(x, str) for x in values_any):
        values = list(values_any)
    elif isinstance(patterns_any, list) and all(isinstance(x, str) for x in patterns_any):
        values = list(patterns_any)
    else:
        values = []

    aliases: dict[str, str]
    if isinstance(aliases_any, dict) and all(
        isinstance(k, str) and isinstance(v, str) for k, v in aliases_any.items()
    ):
        aliases = dict(aliases_any)
    else:
        aliases = {}

    return Whitelist(values=values, aliases=aliases)


def whitelist_hint(
    *, file_name: str, values_key: str, aliases_key: str | None = None
) -> WhitelistHint:
    """Small helper to build `build_whitelist_hints` inputs.

    Keeps call sites readable without introducing a dedicated spec class.
    """

    return (file_name, values_key, aliases_key)


def build_whitelist_hints(
    specs: Iterable[WhitelistHint],
    *,
    base_dir: Path | None = None,
) -> dict[str, Any]:
    """Build adapter hints dict for prompt injection.

    This keeps the IO + validation generic while allowing each domain/prompt to
    decide which whitelist categories to include and what hint keys to use.
    """

    hints: dict[str, Any] = {}

    for file_name, values_key, aliases_key in specs:
        wl = load_whitelist(file_name=file_name, base_dir=base_dir)
        hints[values_key] = wl.values
        if aliases_key:
            hints[aliases_key] = wl.aliases

    return hints
