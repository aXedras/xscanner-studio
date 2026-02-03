"""Diff helpers for order CLI.

This module intentionally does not normalize values; diffs are raw.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DiffEntry:
    path: str
    left: Any
    right: Any


def iter_diff_paths(left: Any, right: Any, *, prefix: str = "") -> Iterable[DiffEntry]:
    if type(left) is not type(right):
        yield DiffEntry(prefix or "$", left, right)
        return

    if isinstance(left, dict):
        left_keys = set(left.keys())
        right_keys = set(right.keys())
        for key in sorted(left_keys | right_keys):
            path = f"{prefix}.{key}" if prefix else str(key)
            if key not in left:
                yield DiffEntry(path, None, right[key])
                continue
            if key not in right:
                yield DiffEntry(path, left[key], None)
                continue
            yield from iter_diff_paths(left[key], right[key], prefix=path)
        return

    if isinstance(left, list):
        max_len = max(len(left), len(right))
        for i in range(max_len):
            path = f"{prefix}[{i}]" if prefix else f"[{i}]"
            if i >= len(left):
                yield DiffEntry(path, None, right[i])
                continue
            if i >= len(right):
                yield DiffEntry(path, left[i], None)
                continue
            yield from iter_diff_paths(left[i], right[i], prefix=path)
        return

    if left != right:
        yield DiffEntry(prefix or "$", left, right)
