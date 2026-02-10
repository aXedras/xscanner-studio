"""Entry point for `python -m cli`.

This provides a simple interactive entry menu so we can host multiple
developer flows under one umbrella CLI.

Non-interactive usage remains available via `python -m cli.cli`.
"""

from __future__ import annotations

import sys


def _dispatch_extract(argv: list[str]) -> int:
    from .cli import main as extract_main

    sys.argv = [sys.argv[0], *argv]
    return int(extract_main())


def _dispatch_orders(argv: list[str]) -> int:
    from .order.cli import main as orders_main

    sys.argv = [sys.argv[0], *argv]
    return int(orders_main())


def main() -> int:
    argv = list(sys.argv[1:])

    # Explicit routing.
    if argv and argv[0] in {"order", "orders"}:
        return _dispatch_orders(argv[1:])
    if argv and argv[0] in {"extract", "bar", "bars"}:
        return _dispatch_extract(argv[1:])

    # If args are provided but no top-level namespace is used, preserve
    # backward compatible behavior by delegating to the existing CLI.
    if argv:
        return _dispatch_extract(argv)

    # Interactive menu (default for `python -m cli` with no args).
    print("\nWas möchtest du anschauen?\n")
    print("  1) Extract (Strategie-Benchmark)")
    print("  2) Orders (manual vs cloud)")

    choice = input("\n🔢 Auswahl [1/2]: ").strip()
    if choice == "2":
        return _dispatch_orders([])
    return _dispatch_extract([])


if __name__ == "__main__":
    raise SystemExit(main())
