"""Order compare HTML report generator."""

from __future__ import annotations

import difflib
import html
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from .template import ORDER_COMPARE_HTML_TEMPLATE


def _safe_json(value: Any) -> str:
    return html.escape(json.dumps(value or {}, ensure_ascii=False, indent=2))


def _badge(*, ok: bool, label: str, kind: str | None = None, title: str | None = None) -> str:
    css = "ok" if ok else "err"
    if kind in {"ok", "warn", "err"}:
        css = kind
    title_attr = f' title="{html.escape(title, quote=True)}"' if title else ""
    return f'<span class="badge {css}"{title_attr}>{html.escape(label)}</span>'


def _confidence_css(score: Any) -> str | None:
    try:
        val = float(score)
    except Exception:
        return None

    if val >= 0.90:
        return "ok"
    if val >= 0.75:
        return "warn"
    return "err"


def _fmt_score(score: Any) -> str | None:
    try:
        return f"{float(score):.2f}"
    except Exception:
        return None


def _render_confidence_badge(meta: dict[str, Any]) -> str | None:
    conf = _as_dict(meta.get("confidence"))
    if not conf:
        return None

    overall = _fmt_score(conf.get("overall"))
    if overall is None:
        return None

    title_parts: list[str] = []
    doc = _fmt_score(conf.get("document_identity"))
    items = _fmt_score(conf.get("order_items"))
    if doc is not None:
        title_parts.append(f"document_identity={doc}")
    if items is not None:
        title_parts.append(f"order_items={items}")

    css = _confidence_css(conf.get("overall")) or "warn"
    title = ", ".join(title_parts) if title_parts else None
    return _badge(ok=True, kind=css, label=f"conf {overall}", title=title)


def _render_readiness_badge(meta: dict[str, Any]) -> str | None:
    readiness = _as_dict(meta.get("readiness"))
    if not readiness:
        return None

    ready = bool(readiness.get("reconciliation_ready"))
    reason = readiness.get("reason")
    title = str(reason) if isinstance(reason, str) and reason.strip() else None
    return _badge(
        ok=ready,
        kind="ok" if ready else "err",
        label="ready" if ready else "not-ready",
        title=title,
    )


def _is_fixture_source(source: Any) -> bool:
    s = str(source or "").lower().strip()
    return s == "fixture" or "fixture" in s


def _render_meta_row(*, source: Any, fixture_name: Any) -> str:
    fixture = str(fixture_name or "").strip()
    src = str(source or "").strip()

    # `source=fixture` is redundant (we already show a badge).
    show_source = bool(src) and not _is_fixture_source(src)

    # Keep a stable single-line meta row so the content below starts aligned.
    parts: list[str] = []
    if fixture:
        parts.append(
            '<span class="meta-k">fixture</span>'
            f'<code class="meta-v" title="{html.escape(fixture, quote=True)}">{html.escape(fixture)}</code>'
        )
    if show_source:
        parts.append(
            '<span class="meta-k">source</span>'
            f'<code class="meta-v" title="{html.escape(src, quote=True)}">{html.escape(src)}</code>'
        )

    inner = "".join(parts)
    return f'<div class="meta-row">{inner}</div>'


def _format_dt(iso: str | None) -> str:
    if not iso:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        return datetime.fromisoformat(iso).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return html.escape(iso)


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


_CURRENCY_SYMBOL_RE = re.compile(r"([\$€£¥])\s+(?=\d)")
_ORDINAL_SPACE_RE = re.compile(r"\b(\d+)\s+(st|nd|rd|th)\b", re.IGNORECASE)
_BIC_SWIFT_LINE_RE = re.compile(r"\b(BIC|SWIFT)\b", re.IGNORECASE)


def _normalize_text_for_raw_diff(text: str) -> str:
    """Normalize cosmetic formatting for raw/marker-text diffs.

    This is intentionally used ONLY for HTML diff rendering. It must not affect
    parsing or persisted fixtures.

    Goals:
    - ignore insignificant whitespace differences (e.g. "$ 1,350.00" vs "$1,350.00")
    - normalize marker pipe separators and key/value spacing
    """

    if not text:
        return ""

    out_lines: list[str] = []
    for raw_ln in text.splitlines():
        ln = raw_ln.rstrip()

        # Currency symbol spacing is a common cosmetic diff across sources.
        ln = _CURRENCY_SYMBOL_RE.sub(r"\1", ln)

        # Common OCR/vision artifact: split ordinals ("5 th" -> "5th").
        ln = _ORDINAL_SPACE_RE.sub(r"\1\2", ln)

        # For BIC/SWIFT lines we normalize away internal spaces in the code token.
        # This keeps real typos visible (e.g. MRMDUS33 vs MRMUDS33) while removing
        # purely cosmetic splits (e.g. MRMDUS 33).
        if _BIC_SWIFT_LINE_RE.search(ln):
            ln = re.sub(
                r"\b([A-Z0-9]{2,}(?:\s+[A-Z0-9]{2,})+)\b",
                lambda m: m.group(1).replace(" ", ""),
                ln,
            )

        stripped = ln.lstrip()
        if stripped.startswith("__"):
            # Normalize marker formatting only (keep raw blocks mostly intact).
            if "|" in ln:
                ln = re.sub(r"\s*\|\s*", " | ", ln)
            if "=" in ln:
                ln = re.sub(r"\s*=\s*", "=", ln)
            ln = re.sub(r"\s{2,}", " ", ln)

        out_lines.append(ln)

    return "\n".join(out_lines)


def _compute_file_src(root_dir: Path, filename: str) -> tuple[str | None, Path]:
    """Return (file_url, abs_path) for a file in root_dir."""

    p = Path(filename)
    if not p.is_absolute():
        p = root_dir / filename
    abs_path = p.resolve()
    if abs_path.exists():
        return f"file://{abs_path.as_posix()}", abs_path
    return None, abs_path


def _build_input_payload_json(*, title: str, root_dir: Path, filenames: list[str]) -> str:
    files: list[dict[str, str]] = []
    for fn in filenames:
        src, abs_path = _compute_file_src(root_dir, fn)
        if not src:
            continue
        ext = abs_path.suffix.lower()
        if ext == ".pdf":
            ftype = "pdf"
        elif ext in {".jpg", ".jpeg", ".png"}:
            ftype = "image"
        else:
            ftype = "file"
        files.append({"name": fn, "url": src, "type": ftype})

    payload = {"title": title, "files": files}
    return json.dumps(payload, ensure_ascii=False)


def _envelope_structured(payload: dict[str, Any] | None) -> dict[str, Any]:
    if not payload:
        return {}
    structured = payload.get("structured_data")
    return structured if isinstance(structured, dict) else {}


def _envelope_raw_text(payload: dict[str, Any] | None) -> str | None:
    if not payload:
        return None
    raw = payload.get("raw")
    if not isinstance(raw, dict):
        return None
    val = raw.get("raw_text")
    return val if isinstance(val, str) and val.strip() else None


def _render_value(value: Any, *, max_chars: int = 180) -> str:
    raw = json.dumps(value, ensure_ascii=False)
    if len(raw) <= max_chars:
        return f'<pre class="diff-pre">{html.escape(raw)}</pre>'
    short = html.escape(raw[:max_chars] + "…")
    full = html.escape(raw)
    return (
        '<details class="diff-details">'
        f'<summary class="muted">{short}</summary>'
        f'<pre class="diff-pre">{full}</pre>'
        "</details>"
    )


def _render_matrix_value(value: Any, *, max_chars: int = 80) -> str:
    raw = json.dumps(value, ensure_ascii=False)
    raw_esc = html.escape(raw, quote=True)
    if len(raw) <= max_chars:
        return f'<span class="matrix-val" title="{raw_esc}">{html.escape(raw)}</span>'
    short = raw[:max_chars] + "…"
    return f'<span class="matrix-val" title="{raw_esc}">{html.escape(short)}</span>'


def _diff_kind(left: Any, right: Any) -> str:
    if left is None and right is not None:
        return "added"
    if left is not None and right is None:
        return "removed"
    return "changed"


def _render_diff_table(diff: dict[str, Any]) -> str:
    entries = diff.get("entries")
    if not isinstance(entries, list) or not entries:
        return '<div class="muted">No diffs</div>'

    rows: list[str] = []
    for e in entries:
        if not isinstance(e, dict):
            continue
        path = str(e.get("path") or "")
        left = e.get("left")
        right = e.get("right")
        kind = _diff_kind(left, right)
        rows.append(
            '<tr class="diff-row '
            + kind
            + '">'
            + f'<td class="diff-path"><code>{html.escape(path)}</code></td>'
            + f'<td class="diff-left">{_render_value(left)}</td>'
            + f'<td class="diff-right">{_render_value(right)}</td>'
            + f'<td class="diff-kind"><span class="badge warn">{html.escape(kind)}</span></td>'
            + "</tr>"
        )

    return (
        '<div class="diff-table-wrap">'
        '<table class="diff-table">'
        "<thead><tr>"
        "<th>Path</th><th>Baseline</th><th>Other</th><th>Kind</th>"
        "</tr></thead>"
        "<tbody>" + "".join(rows) + "</tbody></table></div>"
    )


def _path_tokens(path: str) -> list[str | int]:
    # Supports a subset of JSONPath-like syntax we emit in diffs, e.g.:
    #   parties.seller_name
    #   order_items[0].weight_unit
    tokens: list[str | int] = []
    i = 0
    buf: list[str] = []

    def flush_buf() -> None:
        nonlocal buf
        if buf:
            tokens.append("".join(buf))
            buf = []

    while i < len(path):
        ch = path[i]
        if ch == ".":
            flush_buf()
            i += 1
            continue
        if ch == "[":
            flush_buf()
            j = path.find("]", i + 1)
            if j == -1:
                # malformed; treat rest as a key
                buf.append(path[i:])
                break
            raw = path[i + 1 : j]
            try:
                tokens.append(int(raw))
            except Exception:
                tokens.append(raw)
            i = j + 1
            continue
        buf.append(ch)
        i += 1

    flush_buf()
    return tokens


def _get_value_at_path(root: Any, path: str) -> Any:
    cur: Any = root
    for tok in _path_tokens(path):
        if isinstance(tok, int):
            if not isinstance(cur, list) or tok < 0 or tok >= len(cur):
                return None
            cur = cur[tok]
            continue
        if not isinstance(cur, dict):
            return None
        if tok not in cur:
            return None
        cur = cur[tok]
    return cur


def _collect_diff_paths(compare_payload: dict[str, Any]) -> list[str]:
    comparisons = compare_payload.get("comparisons")
    if not isinstance(comparisons, list):
        return []
    paths: set[str] = set()
    for entry in comparisons:
        if not isinstance(entry, dict):
            continue
        diff = entry.get("diff")
        if not isinstance(diff, dict):
            continue
        entries = diff.get("entries")
        if not isinstance(entries, list):
            continue
        for e in entries:
            if not isinstance(e, dict):
                continue
            p = e.get("path")
            if isinstance(p, str) and p:
                paths.add(p)
    return sorted(paths)


def build_order_diff_matrix(compare_payload: dict[str, Any]) -> str:
    root_dir_raw = compare_payload.get("root_dir")
    root_dir = Path(str(root_dir_raw or ""))
    if not root_dir.is_absolute():
        root_dir = (Path.cwd() / root_dir).resolve()

    baseline = _as_dict(compare_payload.get("baseline"))
    baseline_struct = _envelope_structured(_as_dict(baseline.get("envelope")))

    comparisons = compare_payload.get("comparisons")
    if not isinstance(comparisons, list):
        comparisons = []

    paths = _collect_diff_paths(compare_payload)
    if not paths:
        return '<div class="muted">No diffs found in compare JSON.</div>'

    runs: list[dict[str, Any]] = []
    runs.append(
        {
            "label": str(baseline.get("strategy") or "baseline"),
            "sub": str(baseline.get("file") or ""),
            "structured": baseline_struct,
            "input_payload_json": _build_input_payload_json(
                title=str(baseline.get("file") or "baseline"),
                root_dir=root_dir,
                filenames=[str(baseline.get("file") or "")],
            ),
        }
    )
    for entry in comparisons:
        if not isinstance(entry, dict):
            continue
        structured = _envelope_structured(_as_dict(_as_dict(entry.get("envelope"))))
        run_input = str(entry.get("input") or "")
        runs.append(
            {
                "label": str(entry.get("strategy") or "run"),
                "sub": run_input,
                "structured": structured,
                "input_payload_json": _build_input_payload_json(
                    title=run_input or "Input",
                    root_dir=root_dir,
                    filenames=[s for s in run_input.split("+") if s],
                ),
            }
        )

    # Columns = baseline + runs.
    col_ths: list[str] = ['<th class="matrix-field">Field</th>']
    for run in runs:
        label = html.escape(str(run.get("label") or ""))
        sub = html.escape(str(run.get("sub") or ""))
        payload_json = html.escape(str(run.get("input_payload_json") or ""), quote=True)
        input_btn = (
            f'<button class="btn tiny" data-input="{payload_json}">Input</button>'
            if payload_json
            else ""
        )
        header = (
            '<th class="matrix-run">'
            f'<div class="th-wrap"><span class="th-title">{label}</span>{input_btn}</div>'
            + (f'<div class="muted">{sub}</div>' if sub else "")
            + "</th>"
        )
        col_ths.append(header)

    baseline_values = {p: _get_value_at_path(baseline_struct, p) for p in paths}

    row_parts: list[str] = []
    for p in paths:
        field_cell = (
            '<td class="matrix-field" title="'
            + html.escape(p, quote=True)
            + '"><code>'
            + html.escape(p)
            + "</code></td>"
        )

        tds = [field_cell]
        ref = baseline_values.get(p)
        for idx, run in enumerate(runs):
            structured = run.get("structured")
            v = _get_value_at_path(structured, p)
            if idx == 0:
                kind = "ref"
            else:
                kind = _diff_kind(ref, v) if ref != v else "same"
            cls = f"matrix-cell {kind}"
            tds.append(f'<td class="{cls}">{_render_matrix_value(v, max_chars=90)}</td>')

        row_parts.append("<tr>" + "".join(tds) + "</tr>")

    return (
        '<div class="matrix-wrap">'
        '<table class="matrix-table">'
        "<thead><tr>" + "".join(col_ths) + "</tr></thead>"
        "<tbody>" + "".join(row_parts) + "</tbody></table></div>"
    )


def _render_raw_text_diff(*, baseline_text: str, other_text: str) -> tuple[str, dict[str, int]]:
    baseline_text = _normalize_text_for_raw_diff(baseline_text)
    other_text = _normalize_text_for_raw_diff(other_text)

    base_lines = baseline_text.splitlines()
    other_lines = other_text.splitlines()
    diff = difflib.ndiff(base_lines, other_lines)

    adds = dels = 0
    parts: list[str] = []
    for ln in diff:
        if ln.startswith("? "):
            continue
        if ln.startswith("+ "):
            adds += 1
            cls = "rt-add"
            prefix = "+"
            content = ln[2:]
        elif ln.startswith("- "):
            dels += 1
            cls = "rt-del"
            prefix = "-"
            content = ln[2:]
        else:
            cls = "rt-same"
            prefix = " "
            content = ln[2:] if len(ln) >= 2 else ln

        parts.append(
            f'<div class="rt-line {cls}"><span class="rt-prefix">{html.escape(prefix)}</span>'
            f'<span class="rt-text">{html.escape(content)}</span></div>'
        )

    stats = {"adds": adds, "dels": dels}
    return '<div class="raw-diff">' + "".join(parts) + "</div>", stats


def build_order_raw_text_compare(compare_payload: dict[str, Any]) -> str:
    baseline = _as_dict(compare_payload.get("baseline"))
    baseline_env = _as_dict(baseline.get("envelope"))
    baseline_text = _envelope_raw_text(baseline_env)

    comparisons = compare_payload.get("comparisons")
    if not isinstance(comparisons, list):
        comparisons = []

    # If baseline is missing raw_text, we can't meaningfully diff.
    if not baseline_text:
        return (
            '<div class="muted">'
            "Missing <code>raw.raw_text</code> in baseline envelope. "
            "Record/refresh fixtures with <code>debug=true</code> to include it."
            "</div>"
        )

    blocks: list[str] = []
    for entry in comparisons:
        if not isinstance(entry, dict):
            continue
        env = _as_dict(entry.get("envelope"))
        other_text = _envelope_raw_text(env)
        label = html.escape(str(entry.get("strategy") or "run"))
        inp = html.escape(str(entry.get("input") or ""))

        if not other_text:
            blocks.append(
                '<details class="raw-block">'
                f'<summary>{label} <span class="muted">{inp}</span> — missing raw_text</summary>'
                '<div class="muted" style="margin-top:0.5rem;">'
                "Missing <code>raw.raw_text</code> for this run. "
                "Record/refresh fixtures with <code>debug=true</code> to include it."
                "</div></details>"
            )
            continue

        html_diff, stats = _render_raw_text_diff(baseline_text=baseline_text, other_text=other_text)
        blocks.append(
            '<details class="raw-block">'
            f'<summary>{label} <span class="muted">{inp}</span> '
            f'<span class="badge warn">+{stats["adds"]} / -{stats["dels"]}</span></summary>'
            f'<div style="margin-top:0.65rem;">{html_diff}</div>'
            "</details>"
        )

    if not blocks:
        return '<div class="muted">No comparison runs available.</div>'

    return '<div class="raw-compare">' + "".join(blocks) + "</div>"


def build_order_compare_table(compare_payload: dict[str, Any]) -> str:
    base = html.escape(str(compare_payload.get("base") or ""))

    root_dir_raw = compare_payload.get("root_dir")
    root_dir = Path(str(root_dir_raw or ""))
    if not root_dir.is_absolute():
        root_dir = (Path.cwd() / root_dir).resolve()

    baseline = _as_dict(compare_payload.get("baseline"))
    baseline_raw_text = _envelope_raw_text(_as_dict(baseline.get("envelope")))
    comparisons = compare_payload.get("comparisons")
    if not isinstance(comparisons, list):
        comparisons = []

    # Columns: baseline first, then each comparison (cloud variants).
    columns: list[dict[str, Any]] = []

    columns.append(
        {
            "header": f"{baseline.get('file') or 'baseline'}",
            "strategy": baseline.get("strategy") or "manual",
            "ok": bool(baseline.get("ok", False)),
            "source": baseline.get("source"),
            "fixture_name": baseline.get("fixture_name"),
            "envelope": baseline.get("envelope"),
            "diff": None,
            "error": baseline.get("error"),
            "preview_files": [str(baseline.get("file") or "")],
        }
    )

    for entry in comparisons:
        if not isinstance(entry, dict):
            continue
        columns.append(
            {
                "header": entry.get("input") or "(input)",
                "strategy": entry.get("strategy") or "cloud",
                "ok": bool(entry.get("ok", False)),
                "source": entry.get("source"),
                "fixture_name": entry.get("fixture_name"),
                "envelope": entry.get("envelope"),
                "diff": entry.get("diff"),
                "error": entry.get("error"),
                "preview_files": [s for s in str(entry.get("input") or "").split("+") if s],
            }
        )

    # Build per-column input payload (for the global top preview panel).
    for c in columns:
        preview_files = [s for s in (c.get("preview_files") or []) if isinstance(s, str) and s]
        c["input_payload_json"] = _build_input_payload_json(
            title=str(c.get("header") or "Input"),
            root_dir=root_dir,
            filenames=preview_files,
        )

    # Table: header row = input labels with "Input" button.
    ths_parts: list[str] = []
    for c in columns:
        header = html.escape(str(c.get("header") or ""))
        payload_json = html.escape(str(c.get("input_payload_json") or ""), quote=True)
        input_btn = (
            f'<button class="btn tiny" data-input="{payload_json}">Input</button>'
            if payload_json
            else ""
        )
        ths_parts.append(
            f'<th><div class="th-wrap"><span class="th-title">{header}</span>{input_btn}</div></th>'
        )
    ths = "".join(ths_parts)

    tds: list[str] = []
    for idx, c in enumerate(columns):
        panel_structured_id = f"panel-structured-{idx}"
        panel_envelope_id = f"panel-envelope-{idx}"
        panel_diff_id = f"panel-diff-{idx}"
        panel_raw_id = f"panel-raw-{idx}"

        ok = bool(c.get("ok"))
        strategy = str(c.get("strategy") or "")
        source = c.get("source")
        fixture_name = c.get("fixture_name")
        error = c.get("error")

        badges = [_badge(ok=ok, label=strategy)]
        if fixture_name:
            badges.append(_badge(ok=True, label="fixture", kind="warn"))
        elif source and "live" in str(source):
            badges.append(_badge(ok=True, label="live", kind="warn"))

        env = _as_dict(c.get("envelope"))
        meta = _as_dict(env.get("meta"))

        readiness_badge = _render_readiness_badge(meta)
        if readiness_badge:
            badges.append(readiness_badge)

        confidence_badge = _render_confidence_badge(meta)
        if confidence_badge:
            badges.append(confidence_badge)

        structured = _envelope_structured(env)

        diff = c.get("diff")
        diff_count = None
        if isinstance(diff, dict) and isinstance(diff.get("count"), int):
            diff_count = int(diff.get("count"))

        raw_text = _envelope_raw_text(env)
        raw_panel_html = ""
        raw_btn = ""
        if baseline_raw_text and raw_text:
            if idx == 0:
                raw_panel_html = f'<pre class="raw-pre">{html.escape(raw_text)}</pre>'
                raw_btn = (
                    f'<button class="btn subtle" data-toggle="{panel_raw_id}">Marker Text</button>'
                )
            else:
                diff_html, stats = _render_raw_text_diff(
                    baseline_text=baseline_raw_text,
                    other_text=raw_text,
                )
                raw_btn = (
                    f'<button class="btn subtle" data-toggle="{panel_raw_id}">'
                    f"Marker Text (+{stats['adds']}/-{stats['dels']})"
                    "</button>"
                )
                raw_panel_html = diff_html
        else:
            # Show the toggle but indicate missing raw_text so it's discoverable.
            raw_btn = (
                f'<button class="btn subtle" data-toggle="{panel_raw_id}">Marker Text</button>'
            )
            if not baseline_raw_text:
                raw_panel_html = '<div class="muted">Missing baseline <code>raw.raw_text</code> (record fixtures with debug=true).</div>'
            elif not raw_text:
                raw_panel_html = '<div class="muted">Missing <code>raw.raw_text</code> for this run (record fixtures with debug=true).</div>'

        cell = [
            '<div class="grid">',
            '<div class="cell-top">',
            f'<span class="cell-title">{html.escape(base)}</span>',
            "".join(badges),
            "</div>",
        ]

        cell.append(_render_meta_row(source=source, fixture_name=fixture_name))

        if not ok and error:
            cell.append(
                f'<div class="muted">Error: <span style="color: var(--error);">{html.escape(str(error))}</span></div>'
            )

        preview_files = [s for s in (c.get("preview_files") or []) if isinstance(s, str) and s]
        diff_btn = ""
        if diff is not None:
            label = "Diff" if diff_count is None else f"Diff ({diff_count})"
            diff_btn = f'<button class="btn subtle" data-toggle="{panel_diff_id}">{html.escape(label)}</button>'

        cell.append(
            f'<div style="display:flex; gap:0.5rem; flex-wrap:wrap;">'
            f'<button class="btn subtle" data-toggle="{panel_structured_id}">Structured</button>'
            f'<button class="btn subtle" data-toggle="{panel_envelope_id}">Envelope</button>'
            + raw_btn
            + diff_btn
            + "</div>"
        )

        # No per-column preview in the cell; input is opened via header button.

        cell.append(
            f'<div id="{panel_structured_id}" class="panel"><pre>{_safe_json(structured)}</pre></div>'
        )
        cell.append(
            f'<div id="{panel_envelope_id}" class="panel"><pre>{_safe_json(c.get("envelope"))}</pre></div>'
        )

        cell.append(f'<div id="{panel_raw_id}" class="panel">{raw_panel_html}</div>')

        if diff is not None:
            # Keep this as raw JSON for debugging; the global diff matrix is the main comparison view.
            cell.append(
                f'<div id="{panel_diff_id}" class="panel"><pre>{_safe_json(diff)}</pre></div>'
            )

        cell.append("</div>")
        tds.append(f"<td>{''.join(cell)}</td>")

    return f"<table><thead><tr>{ths}</tr></thead><tbody><tr>{''.join(tds)}</tr></tbody></table>"


def build_order_compare_html(compare_payload: dict[str, Any]) -> str:
    base = html.escape(str(compare_payload.get("base") or ""))
    created_at = _format_dt(str(compare_payload.get("timestamp") or ""))
    root_dir = html.escape(str(compare_payload.get("root_dir") or ""))

    table_html = build_order_compare_table(compare_payload)
    matrix_html = build_order_diff_matrix(compare_payload)
    raw_html = build_order_raw_text_compare(compare_payload)
    return ORDER_COMPARE_HTML_TEMPLATE.format(
        base=base,
        created_at=created_at,
        root_dir=root_dir,
        table_html=table_html,
        matrix_html=matrix_html,
        raw_html=raw_html,
    )


def generate_order_compare_report(*, input_json: Path, output_html: Path | None) -> Path:
    payload = json.loads(input_json.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit("Invalid compare JSON (expected object)")

    if output_html is None:
        # Stable default: if input is compare_<base>.json, write compare_<base>.html.
        if input_json.name.startswith("compare_") and input_json.suffix.lower() == ".json":
            output_html = input_json.with_suffix(".html")
        else:
            out_dir = Path("reports/order")
            out_dir.mkdir(parents=True, exist_ok=True)
            base = str(payload.get("base") or "compare")
            output_html = out_dir / f"compare_{base}.html"

    html_text = build_order_compare_html(payload)
    output_html.write_text(html_text, encoding="utf-8")
    return output_html
