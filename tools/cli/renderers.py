"""HTML rendering functions for benchmark report generation."""

import html
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .report_models import StrategyAggregate


def render_bar(value: float, max_value: float = 1.0) -> str:
    """Render a progress bar with specified value.

    Args:
        value: Current value
        max_value: Maximum value for scaling

    Returns:
        HTML div element styled as progress bar
    """
    width = min(max(value / max_value, 0.0), 1.0) * 100
    return f'<div class="bar" style="width:{width:.1f}%;"></div>'


def compute_image_src(image_value: str, depth: int = 1) -> str:
    """Compute relative image source path for HTML.

    Args:
        image_value: Image path from benchmark results
        depth: Number of directory levels from project root (1 for reports/, 2 for reports/history/)

    Returns:
        Relative path suitable for HTML src attribute
    """
    image_path = Path(image_value)
    if image_path.is_absolute():
        return image_path.as_posix()

    # Build relative path based on depth: ../ for each level
    prefix = "/".join([".."] * depth)
    return f"{prefix}/{image_path.as_posix()}"


def render_structured_data(data: dict[str, Any]) -> str:
    """Render structured data as escaped JSON.

    Args:
        data: Dictionary to render

    Returns:
        HTML-escaped JSON string
    """
    safe_json = json.dumps(data or {}, indent=2, ensure_ascii=False)
    return html.escape(safe_json)


def render_expected_block(entry: dict[str, Any]) -> str:
    """Render expected ground truth metadata block.

    Args:
        entry: Test result entry with expected values

    Returns:
        HTML string for expected metadata card
    """
    expected = entry.get("expected") or {}
    if not isinstance(expected, dict):
        return ""
    fields = expected.get("fields") or {}
    if not fields:
        return ""
    items = [
        f"<li><span>{html.escape(str(label))}</span><strong>{html.escape(str(value))}</strong></li>"
        for label, value in fields.items()
        if value not in (None, "")
    ]
    if not items:
        items.append('<li class="muted">No structured metadata parsed.</li>')
    source = html.escape(str(expected.get("source", "filename")).title())
    return (
        '<div class="expected-card">'
        '<div class="expected-card__top">'
        '<p class="eyebrow">Ground Truth</p>'
        f'<span class="badge neutral">{source}</span>'
        "</div>"
        f"<ul>{''.join(items)}</ul>"
        "</div>"
    )


def render_comparison_block(result: dict[str, Any]) -> str:
    """Render comparison block showing field match results.

    Args:
        result: Strategy result with comparison data

    Returns:
        HTML string showing matched/missing fields
    """
    comparison = result.get("comparison") or {}
    if not isinstance(comparison, dict):
        return ""
    total = comparison.get("total_expected_fields") or 0
    if not total:
        return ""
    matched = comparison.get("matched_fields", 0) or 0
    ratio = f"{matched}/{total}"
    tags = []
    for field_name, is_match in (comparison.get("field_matches") or {}).items():
        css = "ok" if is_match else "miss"
        tags.append(f'<span class="match-tag {css}">{html.escape(str(field_name))}</span>')
    tags_html = "".join(tags) or '<span class="match-tag miss">No fields</span>'
    return (
        '<div class="comparison-block">'
        f'<p class="metric">Ground truth match: <strong>{ratio}</strong></p>'
        f'<div class="match-tags">{tags_html}</div>'
        "</div>"
    )


def render_table_rows(payload: list[dict[str, Any]], depth: int = 1) -> str:
    """Render detailed image test results as HTML cards.

    Args:
        payload: List of all test results
        depth: Number of directory levels from project root (1 for reports/, 2 for reports/history/)

    Returns:
        HTML string with all image result cards
    """
    rows: list[str] = []
    for entry_idx, entry in enumerate(payload):
        image_panel_id = f"image-panel-{entry_idx}"
        image_src = compute_image_src(entry["image"], depth=depth)
        timestamp_display = datetime.fromisoformat(entry["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
        expected_block = render_expected_block(entry)
        rows.append(
            f"""
            <section class=\"image-card\">
                <header>
                    <div>
                        <p class=\"eyebrow\">Image</p>
                        <h2>{html.escape(entry["image"])}</h2>
                    </div>
                    <div class=\"meta\">{html.escape(timestamp_display)}</div>
                </header>
                {expected_block}
                <div class=\"image-tools\">
                    <button class=\"toggle-btn\" data-target=\"{image_panel_id}\">📷 Bild anzeigen</button>
                </div>
                <div id=\"{image_panel_id}\" class=\"toggle-panel image-panel\">
                    <img src=\"{html.escape(image_src)}\" alt=\"{html.escape(entry["image"])}\" loading=\"lazy\" />
                </div>
                <div class=\"strategy-grid\">
            """
        )
        for strategy_idx, (strategy_name, result) in enumerate(entry["results"].items()):
            error = result.get("error")
            confidence = float(result.get("confidence") or 0.0)
            processing_time = float(result.get("processing_time") or 0.0)
            badge_class = "badge error" if error else "badge success"
            badge_label = "Error" if error else "Success"
            data_panel_id = f"data-panel-{entry_idx}-{strategy_idx}"
            structured_data = result.get("structured_data") or {}
            comparison_block = render_comparison_block(result)
            rows.append(
                """
                <article class="strategy-card">
                    <div class="strategy-card__top">
                        <h3>{name}</h3>
                        <span class="{badge_class}">{badge_label}</span>
                    </div>
                    <p class="metric">Confidence: <strong>{confidence:.1%}</strong></p>
                    <div class="metric-bar">
                        {bar}
                    </div>
                    <p class="metric">Time: {time:.2f}s</p>
                    <button class="toggle-btn subtle" data-target="{data_panel_id}">Parsed JSON</button>
                    <div id="{data_panel_id}" class="toggle-panel">
                        <pre>{structured_json}</pre>
                    </div>
                    {comparison_block}
                    {error_block}
                </article>
                """.format(
                    name=strategy_name,
                    badge_class=badge_class,
                    badge_label=badge_label,
                    confidence=confidence,
                    bar=render_bar(confidence),
                    time=processing_time,
                    data_panel_id=data_panel_id,
                    structured_json=render_structured_data(structured_data),
                    comparison_block=comparison_block,
                    error_block=(f'<p class="error-text">{error}</p>' if error else ""),
                )
            )
        rows.append("</div></section>")
    return "\n".join(rows)


def render_summary_chart(aggregates: dict[str, StrategyAggregate]) -> str:
    """Render visual chart showing accuracy vs. processing time.

    Args:
        aggregates: Strategy aggregates to visualize

    Returns:
        HTML string with summary cards grid
    """
    sorted_aggs = sorted(aggregates.values(), key=lambda x: x.avg_conf, reverse=True)
    max_time = max((agg.avg_time for agg in sorted_aggs), default=1.0)

    cards = []
    for agg in sorted_aggs:
        accuracy_pct = agg.avg_conf * 100
        time_bar_width = min((agg.avg_time / max_time) * 100, 100)
        accuracy_color = (
            "#45c486" if accuracy_pct >= 95 else "#ffa726" if accuracy_pct >= 80 else "#ff5f6d"
        )

        cards.append(
            f"""
            <div class="summary-card">
                <div class="summary-card__header">
                    <h3>{html.escape(agg.name)}</h3>
                    <span class="summary-badge" style="background: {accuracy_color}20; color: {accuracy_color};">
                        {accuracy_pct:.1f}%
                    </span>
                </div>
                <div class="summary-metric">
                    <span class="summary-label">Accuracy</span>
                    <div class="summary-bar-container">
                        <div class="summary-bar" style="width: {accuracy_pct:.1f}%; background: {accuracy_color};"></div>
                    </div>
                    <span class="summary-value">{accuracy_pct:.1f}%</span>
                </div>
                <div class="summary-metric">
                    <span class="summary-label">Avg Time</span>
                    <div class="summary-bar-container">
                        <div class="summary-bar time-bar" style="width: {time_bar_width:.1f}%;"></div>
                    </div>
                    <span class="summary-value">{agg.avg_time:.2f}s</span>
                </div>
                <div class="summary-stats">
                    <span>✓ {agg.successes}/{agg.runs} success</span>
                    <span>{agg.success_rate:.0%} success rate</span>
                </div>
            </div>
        """
        )

    return '<div class="summary-grid">' + "".join(cards) + "</div>"


def render_aggregate_table(aggregates: dict[str, StrategyAggregate]) -> str:
    """Render strategy league table with statistics.

    Args:
        aggregates: Strategy aggregates to tabulate

    Returns:
        HTML table rows
    """
    sorted_aggs = sorted(
        aggregates.values(),
        key=lambda item: item.avg_conf,
        reverse=True,
    )
    rows = [
        """
        <tr>
            <th>Strategy</th>
            <th>Success Rate</th>
            <th>Avg Confidence</th>
            <th>Avg Time (s)</th>
            <th>Latest Error</th>
        </tr>
        """
    ]
    for agg in sorted_aggs:
        rows.append(
            """
            <tr>
                <td>{name}</td>
                <td>{success:.0%}</td>
                <td>{confidence:.1%}</td>
                <td>{time:.2f}</td>
                <td>{error}</td>
            </tr>
            """.format(
                name=agg.name,
                success=agg.success_rate,
                confidence=agg.avg_conf,
                time=agg.avg_time,
                error=agg.latest_error or "—",
            )
        )
    return "\n".join(rows)
