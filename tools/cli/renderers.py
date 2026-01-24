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
    """Compute absolute file path for HTML image source.

    Args:
        image_value: Image path from benchmark results

    Returns:
        Absolute file:// URL for the image
    """
    from pathlib import Path

    image_path = Path(image_value)

    # If already absolute, use as-is
    if image_path.is_absolute():
        return f"file://{image_path.as_posix()}"

    # Build absolute path from project root (current working directory)
    project_root = Path.cwd()
    absolute_path = (project_root / image_path).resolve()

    return f"file://{absolute_path.as_posix()}"


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
        HTML string showing matched/missing fields and error details
    """
    comparison = result.get("comparison") or {}
    if not isinstance(comparison, dict):
        return ""
    total = comparison.get("total_expected_fields") or 0
    if not total:
        return ""
    matched = comparison.get("matched_fields", 0) or 0
    ratio = f"{matched}/{total}"

    # Field match tags
    tags = []
    for field_name, is_match in (comparison.get("field_matches") or {}).items():
        css = "ok" if is_match else "miss"
        tags.append(f'<span class="match-tag {css}">{html.escape(str(field_name))}</span>')
    tags_html = "".join(tags) or '<span class="match-tag miss">No fields</span>'

    # Error details
    errors = comparison.get("errors", [])
    error_details = ""
    if errors:
        error_items = "".join(f"<li>{html.escape(str(error))}</li>" for error in errors)
        error_details = f'<ul class="error-list">{error_items}</ul>'

    return (
        '<div class="comparison-block">'
        f'<p class="metric">Ground truth match: <strong>{ratio}</strong></p>'
        f'<div class="match-tags">{tags_html}</div>'
        f"{error_details}"
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
            <section class=\"image-card\" id=\"{image_panel_id}\">
                <header>
                    <div>
                        <p class=\"eyebrow\">Image</p>
                        <h2>{html.escape(entry["image"])}</h2>
                    </div>
                    <div class=\"meta\">{html.escape(timestamp_display)}</div>
                </header>
                {expected_block}
                <div class=\"image-tools\">
                    <button class=\"toggle-btn\" data-target=\"image-preview-{entry_idx}\">📷 Bild anzeigen</button>
                </div>
                <div id=\"image-preview-{entry_idx}\" class=\"toggle-panel image-panel\">
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
    sorted_aggs = sorted(
        aggregates.values(),
        key=lambda x: x.field_accuracy if x.tests_with_ground_truth > 0 else x.avg_conf,
        reverse=True,
    )
    max_time = max((agg.avg_time for agg in sorted_aggs), default=1.0)

    cards = []
    for agg in sorted_aggs:
        # Use field accuracy if available, otherwise confidence
        if agg.tests_with_ground_truth > 0:
            accuracy_pct = agg.field_accuracy * 100
            accuracy_label = "Field Accuracy"
        else:
            accuracy_pct = agg.avg_conf * 100
            accuracy_label = "Confidence"

        time_bar_width = min((agg.avg_time / max_time) * 100, 100)
        accuracy_color = (
            "#45c486" if accuracy_pct >= 95 else "#ffa726" if accuracy_pct >= 80 else "#ff5f6d"
        )

        # Quality stats (if available)
        quality_stats = ""
        if agg.tests_with_ground_truth > 0:
            perfect_rate = agg.perfect_match_rate * 100
            quality_stats = f"<span>🎯 {agg.perfect_matches}/{agg.tests_with_ground_truth} perfect ({perfect_rate:.0f}%)</span>"

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
                    <span class="summary-label">{accuracy_label}</span>
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
                    {quality_stats}
                </div>
            </div>
            """
        )

    return '<div class="summary-grid">' + "".join(cards) + "</div>"


def render_failed_tests_section(payload: list[dict[str, Any]]) -> str:
    """Render section with quick links to tests that failed validation, grouped by strategy.

    Args:
        payload: List of all test results

    Returns:
        HTML string with failed tests section, or empty string if all tests passed
    """
    # Group failed tests by strategy
    failed_by_strategy: dict[str, list[dict]] = {}

    for entry_idx, entry in enumerate(payload):
        image_name = Path(entry["image"]).name

        for strategy_name, result in entry.get("results", {}).items():
            if result.get("error"):
                continue

            comparison = result.get("comparison")
            if comparison and not comparison.get("pass", True):
                matched = comparison.get("matched_fields", 0)
                total = comparison.get("total_expected_fields", 0)

                if strategy_name not in failed_by_strategy:
                    failed_by_strategy[strategy_name] = []

                failed_by_strategy[strategy_name].append(
                    {
                        "idx": entry_idx,
                        "image": image_name,
                        "matched": matched,
                        "total": total,
                        "accuracy": (matched / total * 100) if total > 0 else 0,
                    }
                )

    if not failed_by_strategy:
        return ""

    total_failures = sum(len(tests) for tests in failed_by_strategy.values())

    # Count total tests per strategy
    strategy_total_tests: dict[str, int] = {}
    for entry in payload:
        for strategy_name in entry.get("results", {}).keys():
            strategy_total_tests[strategy_name] = strategy_total_tests.get(strategy_name, 0) + 1

    # Build collapsible sections for each strategy
    strategy_sections = []
    for strategy_idx, (strategy_name, tests) in enumerate(sorted(failed_by_strategy.items())):
        # Sort tests by accuracy (worst first)
        tests.sort(key=lambda x: x["accuracy"])

        # Calculate failure rate and color
        total_tests = strategy_total_tests.get(strategy_name, len(tests))
        failure_rate = len(tests) / total_tests if total_tests > 0 else 0
        failure_color = (
            "#ff5f6d" if failure_rate > 0.2 else "#ffa726" if failure_rate > 0.1 else "#45c486"
        )

        # Build links for this strategy's failed tests
        links = []
        for test in tests:
            test_color = (
                "#45c486"
                if test["accuracy"] >= 80
                else "#ffa726"
                if test["accuracy"] >= 60
                else "#ff5f6d"
            )
            links.append(
                f"""
                <a href="#image-panel-{test["idx"]}" class="failed-test-link">
                    <span class="failed-test-image">{html.escape(test["image"])}</span>
                    <span class="failed-test-badge" style="background: {test_color}20; color: {test_color};">
                        {test["matched"]}/{test["total"]} fields
                    </span>
                </a>
                """
            )

        toggle_id = f"failed-strategy-{strategy_idx}"
        strategy_sections.append(
            f"""
            <div class="failed-strategy-group">
                <div class="failed-strategy-header">
                    <div class="failed-strategy-info">
                        <h3>{html.escape(strategy_name)}</h3>
                        <span class="failed-count">{len(tests)} failed test{"s" if len(tests) != 1 else ""}</span>
                    </div>
                    <div class="failed-strategy-stats">
                        <span class="avg-accuracy-badge" style="background: {failure_color}20; color: {failure_color};">
                            {len(tests)}/{total_tests} failed
                        </span>
                        <button class="toggle-btn subtle" data-target="{toggle_id}">Show</button>
                    </div>
                </div>
                <div id="{toggle_id}" class="toggle-panel">
                    <div class="failed-tests-list">
                        {"".join(links)}
                    </div>
                </div>
            </div>
            """
        )

    return f"""
    <div class="failed-tests-section">
        <h2>⚠️ Tests with Validation Issues ({total_failures})</h2>
        <div class="failed-strategies-container">
            {"".join(strategy_sections)}
        </div>
    </div>
    """


def render_aggregate_table(aggregates: dict[str, StrategyAggregate]) -> str:
    """Render strategy league table with statistics.

    Args:
        aggregates: Strategy aggregates to tabulate

    Returns:
        HTML table rows
    """

    def _rank_value(item: StrategyAggregate) -> float:
        # Prefer ground-truth quality when available; fall back to confidence.
        return item.field_accuracy if item.tests_with_ground_truth > 0 else item.avg_conf

    sorted_aggs = sorted(aggregates.values(), key=_rank_value, reverse=True)
    rows = [
        "<tr>"
        "<th>Strategy</th>"
        "<th>Success Rate</th>"
        "<th>Field Accuracy</th>"
        "<th>Avg Confidence</th>"
        "<th>Avg Time (s)</th>"
        "<th>Latest Error</th>"
        "</tr>"
    ]
    for agg in sorted_aggs:
        field_acc = agg.field_accuracy if agg.tests_with_ground_truth > 0 else 0.0
        field_acc_display = f"{field_acc:.1%}" if agg.tests_with_ground_truth > 0 else "—"
        row_html = (
            "<tr>"
            f"<td>{agg.name}</td>"
            f"<td>{agg.success_rate:.0%}</td>"
            f"<td>{field_acc_display}</td>"
            f"<td>{agg.avg_conf:.1%}</td>"
            f"<td>{agg.avg_time:.2f}</td>"
            f"<td>{agg.latest_error or '—'}</td>"
            "</tr>"
        )
        rows.append(row_html)
    return "\n".join(rows)


def render_metal_accuracy_section(
    metal_aggregates: dict[str, MetalAccuracy],
    strategy_metal_stats: dict[str, dict[str, StrategyMetalStats]] | None = None,
) -> str:
    """Render accuracy breakdown by metal type.

    Args:
        metal_aggregates: Dictionary of metal -> MetalAccuracy

    Returns:
        HTML string for metal accuracy section
    """
    if not metal_aggregates:
        return ""

    # Determine best strategy per metal from the existing matrix input.
    best_by_metal: dict[str, tuple[str, float, float]] = {}
    # value tuple: (strategy_name, field_accuracy, avg_time)
    if strategy_metal_stats:
        for strategy_name, metal_map in strategy_metal_stats.items():
            for metal_name, stats in metal_map.items():
                if not stats.total_fields:
                    # No ground-truth comparisons for this metal/strategy.
                    continue
                candidate = (strategy_name, stats.field_accuracy, stats.avg_time)
                current = best_by_metal.get(metal_name)
                if current is None:
                    best_by_metal[metal_name] = candidate
                    continue
                # Higher accuracy wins; if tied, faster avg time wins.
                if candidate[1] > current[1] or (
                    candidate[1] == current[1] and candidate[2] < current[2]
                ):
                    best_by_metal[metal_name] = candidate

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

        best_line = "—"
        best = best_by_metal.get(metal.metal)
        if best is not None:
            best_name, best_acc, best_time = best
            best_line = f"{html.escape(best_name)} ({best_acc * 100:.1f}%, {best_time:.1f}s)"

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
                        <span class="metal-label">Best Strategy (Field Acc.)</span>
                        <span class="metal-value">{best_line}</span>
                    </div>
                    <div class="metal-stat">
                        <span class="metal-label">Field Accuracy</span>
                        <span class="metal-value">{accuracy_pct:.1f}%</span>
                    </div>
                    <div class="metal-stat">
                        <span class="metal-label">100% Run Pass Rate</span>
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
            {"".join(cards)}
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
                    {"".join(field_rows)}
                </div>
            </div>
        """
        )

    return f"""
    <section class="exec-summary-section">
        <h2>📋 Executive Summary</h2>
        <p class="section-subtitle">Strategy performance ranked by overall field accuracy</p>
        <div class="exec-grid">
            {"".join(cards)}
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
            <thead><tr>{"".join(header_cells)}</tr></thead>
            <tbody>{"".join(rows)}</tbody>
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
                <td><span class="acc-value">{hp.combined_accuracy * 100:.1f}%</span></td>
                <td><span class="acc-value">{hp.individual_a_accuracy * 100:.1f}%</span></td>
                <td><span class="acc-value">{hp.individual_b_accuracy * 100:.1f}%</span></td>
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
            <tbody>{"".join(rows)}</tbody>
        </table>
        <p class="hybrid-note">
            💡 Improvement shows how much better a hybrid could be vs. the best individual model.
            High improvement indicates complementary strengths (e.g., one model better at serial numbers,
            another at producer names).
        </p>
    </section>
    """
