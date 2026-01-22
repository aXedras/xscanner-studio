"""Utilities to hash the Supabase migration SQL files.

Used for generated type freshness checks.
"""

from __future__ import annotations

import hashlib
from pathlib import Path


def compute_migrations_hash(*, migrations_dir: Path) -> tuple[str, list[str]]:
    files = sorted(p for p in migrations_dir.glob("*.sql") if p.is_file())

    digest = hashlib.sha256()
    for file_path in files:
        digest.update(file_path.name.encode("utf-8"))
        digest.update(b"\0")
        # Normalize newlines to keep the hash stable across platforms.
        # Git working trees may contain CRLF on Windows (core.autocrlf), while the
        # repository content is typically LF.
        content = file_path.read_text(encoding="utf-8")
        content = content.replace("\r\n", "\n").replace("\r", "\n")
        digest.update(content.encode("utf-8"))
        digest.update(b"\0")

    return digest.hexdigest(), [p.name for p in files]
