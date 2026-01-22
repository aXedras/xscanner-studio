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
        digest.update(file_path.read_bytes())
        digest.update(b"\0")

    return digest.hexdigest(), [p.name for p in files]
