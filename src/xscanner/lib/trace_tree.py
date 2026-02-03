from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from time import perf_counter
from typing import Any, Literal, TypedDict, TypeGuard, cast

TraceStatus = Literal["ok", "error"]


class TraceArtifact(TypedDict, total=False):
    key: str
    content_type: str
    value: Any
    ref: str
    size: int
    truncated: bool


class TraceSpan(TypedDict, total=False):
    type: Literal["span"]
    id: str
    name: str
    start_ms: float
    end_ms: float
    duration_ms: float
    status: TraceStatus
    summary: str
    attrs: dict[str, Any]
    artifacts: list[TraceArtifact]
    children: list[TraceNode]
    error: dict[str, Any]


class TraceEvent(TypedDict, total=False):
    type: Literal["event"]
    id: str
    name: str
    at_ms: float
    attrs: dict[str, Any]


TraceNode = TraceSpan | TraceEvent


def _is_span(node: TraceNode) -> TypeGuard[TraceSpan]:
    return isinstance(node, dict) and node.get("type") == "span"


def iter_trace_nodes(root: TraceNode) -> Iterator[TraceNode]:
    """Yield nodes in pre-order traversal (span first, then children)."""

    yield root
    if not _is_span(root):
        return

    for child in cast(list[TraceNode], root.get("children") or []):
        if isinstance(child, dict):
            yield from iter_trace_nodes(child)


def iter_trace_spans(root: TraceNode) -> Iterator[TraceSpan]:
    for node in iter_trace_nodes(root):
        if _is_span(node):
            yield node


def _now_ms(t0: float) -> float:
    return round((perf_counter() - t0) * 1000.0, 3)


def _truncate_value(value: Any, *, max_chars: int) -> tuple[Any, int, bool]:
    if isinstance(value, str):
        original_len = len(value)
        if original_len <= max_chars:
            return value, original_len, False
        return value[:max_chars], original_len, True

    # For dict/list: keep as-is; size is not reliable without serialization.
    return value, 0, False


@dataclass
class TraceTree:
    """A lightweight hierarchical trace tree (spans + events).

    This is intended for debug visibility (UI + logs), not for production telemetry.
    """

    root: TraceSpan
    _t0: float
    _stack: list[TraceSpan]

    @staticmethod
    def start(*, name: str, attrs: dict[str, Any] | None = None) -> TraceTree:
        t0 = perf_counter()
        root: TraceSpan = {
            "type": "span",
            "name": name,
            "start_ms": 0.0,
            "status": "ok",
            "attrs": dict(attrs or {}),
            "children": [],
        }
        return TraceTree(root=root, _t0=t0, _stack=[root])

    def finish_ok(self) -> None:
        self._finish(status="ok")

    def finish_error(self, *, error: BaseException) -> None:
        self.root["status"] = "error"
        self.root["error"] = {"type": type(error).__name__, "message": str(error)}
        self._finish(status="error")

    def _finish(self, *, status: TraceStatus) -> None:
        end_ms = _now_ms(self._t0)
        self.root["end_ms"] = end_ms
        self.root["duration_ms"] = round(end_ms - float(self.root.get("start_ms") or 0.0), 3)
        self.root["status"] = status

    @contextmanager
    def span(
        self,
        name: str,
        *,
        attrs: dict[str, Any] | None = None,
        summary: str | None = None,
    ) -> Iterator[TraceSpan]:
        node: TraceSpan = {
            "type": "span",
            "name": name,
            "start_ms": _now_ms(self._t0),
            "status": "ok",
            "attrs": dict(attrs or {}),
            "children": [],
        }
        if summary:
            node["summary"] = summary

        self._stack[-1].setdefault("children", []).append(node)
        self._stack.append(node)

        try:
            yield node
        except Exception as e:
            node["status"] = "error"
            node["error"] = {"type": type(e).__name__, "message": str(e)}
            raise
        finally:
            end_ms = _now_ms(self._t0)
            node["end_ms"] = end_ms
            node["duration_ms"] = round(end_ms - float(node.get("start_ms") or 0.0), 3)
            self._stack.pop()

    def event(self, name: str, *, attrs: dict[str, Any] | None = None) -> TraceEvent:
        ev: TraceEvent = {
            "type": "event",
            "name": name,
            "at_ms": _now_ms(self._t0),
            "attrs": dict(attrs or {}),
        }
        self._stack[-1].setdefault("children", []).append(ev)
        return ev

    def add_artifact(
        self,
        *,
        key: str,
        value: Any,
        content_type: str,
        max_chars: int = 8000,
        ref: str | None = None,
        store_value: bool = True,
    ) -> TraceArtifact:
        size = len(value) if isinstance(value, str) else 0

        artifact: TraceArtifact = {
            "key": key,
            "content_type": content_type,
            "size": size,
        }
        if ref:
            artifact["ref"] = ref

        if store_value:
            truncated_value, _size, truncated = _truncate_value(value, max_chars=max_chars)
            artifact["value"] = truncated_value
            artifact["size"] = _size
            artifact["truncated"] = truncated
        self._stack[-1].setdefault("artifacts", []).append(artifact)
        return artifact


def format_trace_tree(root: TraceSpan, *, indent: str = "  ") -> str:
    """Pretty-print trace tree as a human-readable log string."""

    lines: list[str] = []

    def _fmt_duration(node: TraceSpan) -> str:
        d = node.get("duration_ms")
        if isinstance(d, (int, float)):
            return f"{round(float(d))}ms"
        return "?ms"

    def _fmt_status(node: TraceSpan) -> str:
        s = node.get("status")
        return str(s) if isinstance(s, str) else "ok"

    def _fmt_summary(node: TraceSpan) -> str:
        summary = node.get("summary")
        if isinstance(summary, str) and summary:
            return f" | {summary}"
        attrs = node.get("attrs")
        if isinstance(attrs, dict):
            # Keep log compact: show a few common keys if present.
            parts: list[str] = []
            for k in ("strategy", "strategy_impl", "issuer", "provider", "model", "attempt"):
                if k in attrs and attrs.get(k) is not None:
                    parts.append(f"{k}={attrs.get(k)}")
            if parts:
                return " | " + ", ".join(parts)
        return ""

    def _walk(node: TraceNode, depth: int) -> None:
        pad = indent * depth
        if node.get("type") == "event":
            at_ms = node.get("at_ms")
            ts = f"@{round(float(at_ms))}ms" if isinstance(at_ms, (int, float)) else "@?ms"
            lines.append(f"{pad}• {node.get('name')} {ts}")
            return

        # span
        span = cast(TraceSpan, node)
        name = node.get("name")
        lines.append(
            f"{pad}▶ {name} ({_fmt_duration(span)}, {_fmt_status(span)}){_fmt_summary(span)}"
        )

        err = node.get("error")
        if isinstance(err, dict) and err.get("message"):
            lines.append(f"{pad}{indent}! {err.get('type')}: {err.get('message')}")

        for child in cast(list[TraceNode], span.get("children") or []):
            if isinstance(child, dict):
                _walk(child, depth + 1)

    _walk(root, 0)
    return "\n".join(lines)
