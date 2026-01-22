"""Check that generated server DB types match current migrations.

Fails when `supabase/migrations/*.sql` changed but `src/xscanner/server/db_types.py`
was not regenerated.

Usage:
  python -m scripts.db.check_db_types
"""

from __future__ import annotations

import re
from pathlib import Path

from scripts.db.schema_hash import compute_migrations_hash


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    migrations_dir = repo_root / "supabase" / "migrations"
    types_file = repo_root / "src" / "xscanner" / "server" / "db_types.py"

    expected_hash, _ = compute_migrations_hash(migrations_dir=migrations_dir)

    if not types_file.exists():
        raise SystemExit(
            "[db-types] Missing generated types file. Run: python -m scripts.db.gen_db_types"
        )

    content = types_file.read_text(encoding="utf-8")
    match = re.search(r"SCHEMA_HASH:\s*str\s*=\s*\"([a-f0-9]{64})\"", content, re.IGNORECASE)
    found = match.group(1) if match else None

    if not found:
        raise SystemExit(
            "[db-types] Could not find SCHEMA_HASH in generated types file. Run: python -m scripts.db.gen_db_types"
        )

    if found != expected_hash:
        raise SystemExit(
            "[db-types] Server DB types are out of date. Run: python -m scripts.db.gen_db_types"
        )

    print("[db-types] Server DB types are up to date.")


if __name__ == "__main__":
    main()
