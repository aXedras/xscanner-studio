"""HTML rendering functions for benchmark report generation."""

import html
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .report_models import HybridPotential, MetalAccuracy, StrategyAggregate, StrategyMetalStats


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


def compute_image_src(image_value: str) -> str:
    """Compute relative image source path for HTML.

    Args:
        image_value: Image path from benchmark results

    Returns:
        Relative path suitable for HTML src attribute
    """
    image_path = Path(image_value)
    if image_path.is_absolute():
        return image_path.as_posix()
    return (Path("..") / image_path).as_posix()


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


def render_table_rows(payload: list[dict[str, Any]]) -> str:
    """Render detailed image test results as HTML cards.

    Args:
        payload: List of all test results

    Returns:
        HTML string with all image result cards
    """
    rows: list[str] = []
    for entry_idx, entry in enumerate(payload):
        image_panel_id = f"image-panel-{entry_idx}"
        image_src = compute_image_src(entry["image"])
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


def render_metal_accuracy_section(metal_aggregates: dict[str, MetalAccuracy]) -> str:
    """Render accuracy breakdown by metal type.

    Args:
        metal_aggregates: Dictionary of metal -> MetalAccuracy

    Returns:
        HTML string for metal accuracy section
    """
    if not metal_aggregates:
        return ""

    # Sort by field accuracy descending
    sorted_metals = sorted(
        metal_aggregates.values(),
        key=lambda m: m.field_accuracy,
        reverse=True,
    )

    # Metal-specific colors
    metal_colors = {
        "Gold": "#FFD700",
        "Silver": "#C0C0C0",
        "Platinum": "#E5E4E2",
        "Palladium": "#CED0DD",
    }

    cards = []
    for metal in sorted_metals:
        color = metal_colors.get(metal.metal, "#888888")
        accuracy_pct = metal.field_accuracy * 100
        pass_rate_pct = metal.full_pass_rate * 100

        # Color based on accuracy
        status_color = (
            "#45c486" if accuracy_pct >= 90 else "#ffa726" if accuracy_pct >= 70 else "#ff5f6d"
        )

        cards.append(
            f"""
            <div class="metal-card" style="border-left: 4px solid {color};">
                <div class="metal-card__header">
                    <h3 style="color: {color};">{html.escape(metal.metal)}</h3>
                    <span class="metal-badge" style="background: {status_color}20; color: {status_color};">
                        {accuracy_pct:.1f}%
                    </span>
                </div>
                <div class="metal-stats">
                    <div class="metal-stat">
                        <span class="metal-label">Images</span>
                        <span class="metal-value">{metal.total_images}</span>
                    </div>
                    <div class="metal-stat">
                        <span class="metal-label">Field Accuracy</span>
                        <span class="metal-value">{accuracy_pct:.1f}%</span>
                    </div>
                    <div class="metal-stat">
                        <span class="metal-label">100% Pass Rate</span>
                        <span class="metal-value">{pass_rate_pct:.1f}%</span>
                    </div>
                    <div class="metal-stat">
                        <span class="metal-label">Fields Matched</span>
                        <span class="metal-value">{metal.total_matches}/{metal.total_fields}</span>
                    </div>
                </div>
            </div>
            """
        )

    return f"""
    <section class="metal-accuracy-section">
        <h2>📊 Accuracy by Metal Type</h2>
        <p class="section-subtitle">Field-level accuracy across different precious metals</p>
        <div class="metal-grid">
            {''.join(cards)}
        </div>
    </section>
    """


def render_executive_summary(aggregates: dict[str, StrategyAggregate]) -> str:
    """Render executive summary with key metrics per strategy.

    Shows: avg accuracy, avg time, field-level breakdown, ranking
    """
    if not aggregates:
        return ""

    # Sort by field accuracy
    sorted_aggs = sorted(
        aggregates.values(),
        key=lambda x: x.field_accuracy,
        reverse=True,
    )

    fields = ["SerialNumber", "Metal", "Weight", "WeightUnit", "Fineness", "Producer"]

    # Build strategy cards
    cards = []
    for rank, agg in enumerate(sorted_aggs, 1):
        accuracy_pct = agg.field_accuracy * 100

        # Color based on accuracy
        if accuracy_pct >= 80:
            rank_color = "#45c486"  # Green
        elif accuracy_pct >= 60:
            rank_color = "#ffa726"  # Orange
        else:
            rank_color = "#ff5f6d"  # Red

        # Field breakdown
        field_rows = []
        for fld in fields:
            fld_acc = agg.get_field_accuracy(fld) * 100
            fld_color = "#45c486" if fld_acc >= 80 else "#ffa726" if fld_acc >= 50 else "#ff5f6d"
            field_rows.append(
                f'<div class="field-stat">'
                f'<span class="field-name">{fld}</span>'
                f'<span class="field-acc" style="color: {fld_color};">{fld_acc:.0f}%</span>'
                f"</div>"
            )

        cards.append(
            f"""
            <div class="exec-card">
                <div class="exec-rank" style="background: {rank_color};">#{rank}</div>
                <div class="exec-header">
                    <h3>{html.escape(agg.name)}</h3>
                    <span class="exec-accuracy">{accuracy_pct:.1f}%</span>
                </div>
                <div class="exec-metrics">
                    <div class="exec-metric">
                        <span class="metric-label">Avg Time</span>
                        <span class="metric-value">{agg.avg_time:.1f}s</span>
                    </div>
                    <div class="exec-metric">
                        <span class="metric-label">Success Rate</span>
                        <span class="metric-value">{agg.success_rate:.0%}</span>
                    </div>
                    <div class="exec-metric">
                        <span class="metric-label">Images</span>
                        <span class="metric-value">{agg.runs}</span>
                    </div>
                </div>
                <div class="exec-fields">
                    <h4>Field Accuracy</h4>
                    {''.join(field_rows)}
                </div>
            </div>
        """
        )

    return f"""
    <section class="exec-summary-section">
        <h2>📋 Executive Summary</h2>
        <p class="section-subtitle">Strategy performance ranked by overall field accuracy</p>
        <div class="exec-grid">
            {''.join(cards)}
        </div>
    </section>
    """


def render_strategy_metal_matrix(
    strategy_metal_stats: dict[str, dict[str, StrategyMetalStats]],
) -> str:
    """Render matrix showing strategy performance per metal type."""
    if not strategy_metal_stats:
        return ""

    # Get all metals
    all_metals = set()
    for strat_data in strategy_metal_stats.values():
        all_metals.update(strat_data.keys())
    metals = sorted(all_metals)

    if not metals:
        return ""

    # Metal colors
    metal_colors = {
        "Gold": "#FFD700",
        "Silver": "#C0C0C0",
        "Platinum": "#E5E4E2",
        "Palladium": "#CED0DD",
    }

    # Build table
    header_cells = ["<th>Strategy</th>"]
    for metal in metals:
        color = metal_colors.get(metal, "#888")
        header_cells.append(f'<th style="color: {color};">{metal}</th>')
    header_cells.append("<th>Avg Time</th>")

    rows = []
    for strategy_name, metal_data in strategy_metal_stats.items():
        row_cells = [f'<td class="strategy-name">{html.escape(strategy_name)}</td>']
        total_time = 0
        total_images = 0

        for metal in metals:
            stats = metal_data.get(metal)
            if stats:
                acc = stats.field_accuracy * 100
                color = "#45c486" if acc >= 80 else "#ffa726" if acc >= 60 else "#ff5f6d"
                row_cells.append(
                    f'<td><span class="matrix-acc" style="background: {color}20; color: {color};">'
                    f"{acc:.0f}%</span></td>"
                )
                total_time += stats.total_time
                total_images += stats.total_images
            else:
                row_cells.append("<td>—</td>")

        avg_time = total_time / total_images if total_images else 0
        row_cells.append(f"<td>{avg_time:.1f}s</td>")
        rows.append("<tr>" + "".join(row_cells) + "</tr>")

    return f"""
    <section class="matrix-section">
        <h2>🎯 Strategy Performance by Metal</h2>
        <p class="section-subtitle">Field accuracy breakdown per strategy and metal type</p>
        <table class="matrix-table">
            <thead><tr>{''.join(header_cells)}</tr></thead>
            <tbody>{''.join(rows)}</tbody>
        </table>
    </section>
    """


def render_hybrid_analysis(hybrid_potentials: list[HybridPotential]) -> str:
    """Render analysis of potential hybrid strategy combinations."""
    if not hybrid_potentials:
        return ""

    # Show top 5 combinations
    top_combos = hybrid_potentials[:5]

    rows = []
    for hp in top_combos:
        improvement = hp.combined_accuracy - max(hp.individual_a_accuracy, hp.individual_b_accuracy)
        improvement_pct = improvement * 100

        # Color based on improvement potential
        if improvement_pct >= 5:
            imp_color = "#45c486"
            imp_icon = "📈"
        elif improvement_pct >= 2:
            imp_color = "#ffa726"
            imp_icon = "➡️"
        else:
            imp_color = "#888"
            imp_icon = "➖"

        # Field complementarity - which model is better for which field
        comp_items = []
        for field, winner in hp.field_complementarity.items():
            short_winner = winner.split()[0][:8]  # Shorten name
            comp_items.append(f'<span class="field-winner">{field}: {short_winner}</span>')

        rows.append(
            f"""
            <tr>
                <td>
                    <div class="combo-names">
                        <span class="strat-a">{html.escape(hp.strategy_a)}</span>
                        <span class="combo-plus">+</span>
                        <span class="strat-b">{html.escape(hp.strategy_b)}</span>
                    </div>
                </td>
                <td><span class="acc-value">{hp.combined_accuracy*100:.1f}%</span></td>
                <td><span class="acc-value">{hp.individual_a_accuracy*100:.1f}%</span></td>
                <td><span class="acc-value">{hp.individual_b_accuracy*100:.1f}%</span></td>
                <td>
                    <span class="improvement" style="color: {imp_color};">
                        {imp_icon} +{improvement_pct:.1f}%
                    </span>
                </td>
                <td>{hp.avg_time_combined:.1f}s</td>
            </tr>
        """
        )

    return f"""
    <section class="hybrid-section">
        <h2>🔀 Hybrid Strategy Potential</h2>
        <p class="section-subtitle">
            Theoretical accuracy if combining best field results from two strategies.
            Higher improvement = models complement each other well.
        </p>
        <table class="hybrid-table">
            <thead>
                <tr>
                    <th>Combination</th>
                    <th>Combined Acc.</th>
                    <th>Model A Acc.</th>
                    <th>Model B Acc.</th>
                    <th>Improvement</th>
                    <th>Est. Time</th>
                </tr>
            </thead>
            <tbody>{''.join(rows)}</tbody>
        </table>
        <p class="hybrid-note">
            💡 Improvement shows how much better a hybrid could be vs. the best individual model.
            High improvement indicates complementary strengths (e.g., one model better at serial numbers,
            another at producer names).
        </p>
    </section>
    """
