"""Generate Python TypedDicts from Supabase migrations.

This is intentionally minimal: it parses the `CREATE TABLE extraction (...)` definition
from `supabase/migrations/*.sql` and generates strongly-typed dictionaries for the
server persistence layer.

Why:
- Keep server code typed without manually updating models on every schema change.
- Fail fast in CI/pre-commit when migrations drift.

Usage:
  python -m scripts.db.gen_db_types

Notes:
- This generator expects a local, repo-managed schema (migrations) and does not
  require a live database connection.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from scripts.db.schema_hash import compute_migrations_hash


@dataclass(frozen=True)
class Column:
    name: str
    pg_type: str
    not_null: bool
    has_default: bool


_CREATE_TABLE_RE = re.compile(
    r"CREATE\s+TABLE\s+(?P<table>\w+)\s*\((?P<body>.*?)\)\s*;",
    re.IGNORECASE | re.DOTALL,
)


def _strip_sql_comments(sql: str) -> str:
    sql = re.sub(r"--.*?$", "", sql, flags=re.MULTILINE)
    # Remove /* ... */ blocks
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
    return sql


def _split_columns(body: str) -> list[str]:
    # Split on commas at top-level (no parentheses nesting expected for our table)
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    for ch in body:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)

        if ch == "," and depth == 0:
            item = "".join(current).strip()
            if item:
                parts.append(item)
            current = []
            continue

        current.append(ch)

    tail = "".join(current).strip()
    if tail:
        parts.append(tail)
    return parts


def _parse_column(defn: str) -> Column | None:
    defn = defn.strip()
    if not defn:
        return None

    # Skip constraints/index definitions if they appear inside table body.
    if re.match(r"^(CONSTRAINT|PRIMARY\s+KEY|UNIQUE|FOREIGN\s+KEY)\b", defn, re.IGNORECASE):
        return None

    # Matches: name TYPE [NOT NULL] [DEFAULT ...]
    #
    # Notes:
    # - Types can be custom enums like `extraction_status` (lowercase + underscores)
    # - Types can have size/precision like VARCHAR(255)
    m = re.match(
        r"^(?P<name>[a-zA-Z_][\w]*)\s+(?P<type>[a-zA-Z_][\w]*(?:\([^)]+\))?)\b(?P<rest>.*)$",
        defn,
    )
    if not m:
        return None

    name = m.group("name")
    pg_type = m.group("type").strip().upper()
    rest = m.group("rest").upper()

    not_null = "NOT NULL" in rest or "PRIMARY KEY" in rest
    has_default = "DEFAULT" in rest

    return Column(name=name, pg_type=pg_type, not_null=not_null, has_default=has_default)


def _pg_to_py_type(pg_type: str) -> str:
    base = pg_type.upper()

    if base.startswith("UUID"):
        return "str"
    if base.startswith("TEXT"):
        return "str"
    if base.startswith("TIMESTAMPTZ") or base.startswith("TIMESTAMP"):
        return "str"
    if base.startswith("FLOAT") or base.startswith("DOUBLE") or base.startswith("REAL"):
        return "float"
    if base.startswith("BOOLEAN"):
        return "bool"
    if base.startswith("JSONB") or base.startswith("JSON"):
        return "dict[str, Any]"

    # Fallback: keep it as Any to avoid false certainty.
    return "Any"


def _render_typed_dict(*, name: str, columns: list[Column], use_not_required: bool) -> str:
    lines: list[str] = []
    lines.append(
        f"class {name}(TypedDict):"
        if not use_not_required
        else f"class {name}(TypedDict, total=False):"
    )

    if not columns:
        lines.append("    pass")
        return "\n".join(lines)

    for col in columns:
        py_type = _pg_to_py_type(col.pg_type)

        # total=False already makes keys optional, but the value type should still
        # reflect whether the column can be NULL.
        if not col.not_null:
            py_type = f"{py_type} | None"

        lines.append(f"    {col.name}: {py_type}")

    return "\n".join(lines)


def _extract_table_columns(*, migrations_dir: Path, table: str) -> list[Column]:
    sql = "\n".join(p.read_text(encoding="utf-8") for p in sorted(migrations_dir.glob("*.sql")))
    sql = _strip_sql_comments(sql)

    for match in _CREATE_TABLE_RE.finditer(sql):
        if match.group("table").lower() != table.lower():
            continue

        body = match.group("body")
        parts = _split_columns(body)
        columns: list[Column] = []
        for part in parts:
            col = _parse_column(part)
            if col:
                columns.append(col)

        if columns:
            return columns

    raise RuntimeError(f"Could not find CREATE TABLE {table} in migrations")


def generate(*, repo_root: Path) -> str:
    migrations_dir = repo_root / "supabase" / "migrations"
    schema_hash, files = compute_migrations_hash(migrations_dir=migrations_dir)

    columns = _extract_table_columns(migrations_dir=migrations_dir, table="extraction")

    # Row is always complete and typed; Insert is intentionally permissive (total=False)
    # because Postgres defaults and service-layer behavior may omit keys.
    row = _render_typed_dict(name="ExtractionRow", columns=columns, use_not_required=False)
    insert = _render_typed_dict(name="ExtractionInsert", columns=columns, use_not_required=True)

    header = (
        '"""AUTO-GENERATED FILE. DO NOT EDIT MANUALLY.\n\n'
        "Generated by: python -m scripts.db.gen_db_types\n"
        f"Source: supabase/migrations/*.sql (hash: {schema_hash})\n"
        f"Files: {', '.join(files)}\n"
        '"""\n\n'
    )

    imports = (
        "from __future__ import annotations\n\n"
        "from typing import Any, TypedDict\n\n"
        f'SCHEMA_HASH: str = "{schema_hash}"\n\n\n'
    )

    # PEP8: keep two blank lines between top-level classes.
    return header + imports + row + "\n\n\n" + insert + "\n"


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    out_file = repo_root / "src" / "xscanner" / "server" / "db_types.py"

    content = generate(repo_root=repo_root)
    out_file.write_text(content, encoding="utf-8")

    try:
        subprocess.run(
            ["ruff", "format", str(out_file)],
            cwd=str(repo_root),
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception as e:
        print(f"[db-types] ruff format failed (continuing): {e}")

    print(f"[db-types] wrote {out_file.relative_to(repo_root)}")


if __name__ == "__main__":
    main()
