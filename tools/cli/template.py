"""HTML template for benchmark report generation."""

# HTML template with placeholders for dynamic content
# Template uses double braces {{}} for CSS that should not be formatted
# and single braces {} for Python format() placeholders
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta http-equiv="X-UA-Compatible" content="IE=edge" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>xScanner Strategy Benchmark</title>
    <style>
        :root {{
            --bg: #0b1221;
            --card-bg: #111b2f;
            --surface: #16223b;
            --text: #f4f7ff;
            --muted: #8ea2c4;
            --accent: #4ad4ff;
            --success: #45c486;
            --error: #ff5f6d;
        }}
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0;
            background: linear-gradient(130deg, #050910, #101b33);
            font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
            color: var(--text);
            line-height: 1.5;
            padding: 2rem;
        }}
        h1 {{ margin-top: 0; font-size: 2.5rem; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        header.hero {{
            background: var(--card-bg);
            padding: 2rem;
            border-radius: 20px;
            box-shadow: 0 25px 60px rgba(5, 10, 20, 0.45);
            margin-bottom: 2rem;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }}
        .meta {{ color: var(--muted); font-size: 0.9rem; }}
        table {{ width: 100%; border-collapse: collapse; margin: 1rem 0 2.5rem; }}
        th, td {{ padding: 0.75rem 1rem; text-align: left; }}
        th {{ background: var(--surface); }}
        tr:nth-child(even) td {{ background: rgba(255,255,255,0.02); }}
        tr:nth-child(odd) td {{ background: rgba(255,255,255,0.04); }}
        .image-card {{
            background: var(--card-bg);
            border-radius: 18px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }}
        .expected-card {{
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 14px;
            padding: 1rem;
            margin-bottom: 1rem;
        }}
        .expected-card__top {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
        }}
        .expected-card ul {{
            list-style: none;
            padding: 0;
            margin: 0;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 0.5rem;
        }}
        .expected-card li {{
            background: rgba(255,255,255,0.02);
            border-radius: 10px;
            padding: 0.5rem 0.75rem;
            font-size: 0.85rem;
            display: flex;
            flex-direction: column;
            gap: 0.15rem;
        }}
        .expected-card li span {{
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-size: 0.7rem;
            color: var(--muted);
        }}
        .image-tools {{
            display: flex;
            gap: 0.5rem;
            margin-bottom: 0.75rem;
        }}
        .image-card header {{
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            flex-wrap: wrap;
            gap: 1rem;
            border-bottom: 1px solid rgba(255,255,255,0.08);
            padding-bottom: 1rem;
            margin-bottom: 1.5rem;
        }}
        .eyebrow {{
            text-transform: uppercase;
            letter-spacing: 0.15em;
            font-size: 0.75rem;
            color: var(--muted);
            margin: 0;
        }}
        .strategy-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
        }}
        .strategy-card {{
            background: var(--surface);
            border-radius: 14px;
            padding: 1rem;
            min-height: 180px;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }}
        .toggle-btn {{
            background: rgba(74, 212, 255, 0.15);
            color: var(--text);
            border: 1px solid rgba(74, 212, 255, 0.4);
            border-radius: 999px;
            padding: 0.25rem 0.75rem;
            font-size: 0.8rem;
            cursor: pointer;
            transition: background 0.2s ease, color 0.2s ease;
        }}
        .toggle-btn.subtle {{
            align-self: flex-start;
            background: rgba(255,255,255,0.05);
            border-color: rgba(255,255,255,0.12);
        }}
        .toggle-btn.is-active {{
            background: var(--accent);
            color: #03121f;
        }}
        .toggle-panel {{
            display: none;
            border-radius: 12px;
            background: rgba(255,255,255,0.04);
            padding: 0.75rem;
            margin-top: 0.5rem;
        }}
        .toggle-panel.is-open {{
            display: block;
        }}
        .toggle-panel pre {{
            margin: 0;
            font-size: 0.8rem;
            color: var(--muted);
            white-space: pre-wrap;
            word-break: break-word;
        }}
        .image-panel img {{
            max-width: 100%;
            border-radius: 12px;
            border: 1px solid rgba(255,255,255,0.08);
            box-shadow: 0 10px 30px rgba(0,0,0,0.4);
        }}
        .strategy-card__top {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 0.5rem;
        }}
        .badge {{
            padding: 0.1rem 0.6rem;
            border-radius: 999px;
            font-size: 0.75rem;
        }}
        .badge.success {{ background: rgba(69,196,134,0.2); color: var(--success); }}
        .badge.error {{ background: rgba(255,95,109,0.2); color: var(--error); }}
        .badge.neutral {{ background: rgba(255,255,255,0.15); color: var(--text); }}
        .metric {{ margin: 0; font-size: 0.95rem; color: var(--muted); }}
        .metric strong {{ color: var(--text); }}
        .comparison-block {{
            margin-top: 0.5rem;
            padding-top: 0.5rem;
            border-top: 1px solid rgba(255,255,255,0.08);
        }}
        .match-tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.35rem;
            margin-top: 0.4rem;
        }}
        .match-tag {{
            border-radius: 999px;
            padding: 0.15rem 0.6rem;
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }}
        .match-tag.ok {{ background: rgba(69,196,134,0.15); color: var(--success); }}
        .match-tag.miss {{ background: rgba(255,95,109,0.15); color: var(--error); }}
        .metric-bar {{
            width: 100%; height: 6px;
            background: rgba(255,255,255,0.1);
            border-radius: 999px;
            overflow: hidden;
        }}
        .bar {{
            height: 100%;
            background: linear-gradient(90deg, #4ad4ff, #47f0c2);
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.25rem;
            margin: 2rem 0;
        }}
        .summary-card {{
            background: var(--surface);
            border-radius: 16px;
            padding: 1.25rem;
            border: 1px solid rgba(255,255,255,0.08);
        }}
        .summary-card__header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }}
        .summary-card h3 {{
            margin: 0;
            font-size: 1.1rem;
            font-weight: 600;
        }}
        .summary-badge {{
            padding: 0.25rem 0.75rem;
            border-radius: 999px;
            font-size: 0.85rem;
            font-weight: 600;
        }}
        .summary-metric {{
            margin-bottom: 0.75rem;
        }}
        .summary-label {{
            display: block;
            font-size: 0.75rem;
            color: var(--muted);
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 0.35rem;
        }}
        .summary-bar-container {{
            position: relative;
            height: 8px;
            background: rgba(255,255,255,0.1);
            border-radius: 999px;
            overflow: hidden;
            margin-bottom: 0.25rem;
        }}
        .summary-bar {{
            height: 100%;
            border-radius: 999px;
            transition: width 0.3s ease;
        }}
        .summary-bar.time-bar {{
            background: linear-gradient(90deg, #4ad4ff, #9c27b0);
        }}
        .summary-value {{
            font-size: 0.95rem;
            font-weight: 600;
            color: var(--text);
        }}
        .summary-stats {{
            display: flex;
            justify-content: space-between;
            font-size: 0.8rem;
            color: var(--muted);
            padding-top: 0.75rem;
            border-top: 1px solid rgba(255,255,255,0.08);
        }}
        .error-text {{
            color: var(--error);
            font-size: 0.8rem;
            background: rgba(255,95,109,0.08);
            padding: 0.4rem 0.6rem;
            border-radius: 10px;
        }}
        /* Metal Accuracy Section */
        .metal-accuracy-section {{
            background: var(--card-bg);
            border-radius: 18px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }}
        .metal-accuracy-section h2 {{
            margin: 0 0 0.25rem 0;
        }}
        .section-subtitle {{
            color: var(--muted);
            margin: 0 0 1.25rem 0;
            font-size: 0.95rem;
        }}
        .metal-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 1rem;
        }}
        .metal-card {{
            background: var(--surface);
            border-radius: 14px;
            padding: 1rem;
        }}
        .metal-card__header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.75rem;
        }}
        .metal-card h3 {{
            margin: 0;
            font-size: 1.2rem;
            font-weight: 700;
        }}
        .metal-badge {{
            padding: 0.2rem 0.7rem;
            border-radius: 999px;
            font-size: 0.85rem;
            font-weight: 600;
        }}
        .metal-stats {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 0.5rem;
        }}
        .metal-stat {{
            background: rgba(255,255,255,0.03);
            border-radius: 10px;
            padding: 0.5rem 0.75rem;
            display: flex;
            flex-direction: column;
            gap: 0.1rem;
        }}
        .metal-label {{
            font-size: 0.7rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--muted);
        }}
        .metal-value {{
            font-size: 1rem;
            font-weight: 600;
            color: var(--text);
        }}
        /* Executive Summary Section */
        .exec-summary-section {{
            background: var(--card-bg);
            border-radius: 18px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }}
        .exec-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1rem;
        }}
        .exec-card {{
            background: var(--surface);
            border-radius: 14px;
            padding: 1.25rem;
            position: relative;
        }}
        .exec-rank {{
            position: absolute;
            top: -8px;
            left: -8px;
            width: 36px;
            height: 36px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 0.9rem;
            color: white;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }}
        .exec-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
            padding-left: 1.5rem;
        }}
        .exec-header h3 {{
            margin: 0;
            font-size: 1rem;
        }}
        .exec-accuracy {{
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--accent);
        }}
        .exec-metrics {{
            display: flex;
            gap: 1rem;
            margin-bottom: 1rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid rgba(255,255,255,0.08);
        }}
        .exec-metric {{
            display: flex;
            flex-direction: column;
            gap: 0.1rem;
        }}
        .metric-label {{
            font-size: 0.7rem;
            text-transform: uppercase;
            color: var(--muted);
        }}
        .metric-value {{
            font-weight: 600;
        }}
        .exec-fields h4 {{
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--muted);
            margin: 0 0 0.5rem 0;
        }}
        .field-stat {{
            display: flex;
            justify-content: space-between;
            padding: 0.25rem 0;
            border-bottom: 1px solid rgba(255,255,255,0.04);
        }}
        .field-name {{
            font-size: 0.85rem;
            color: var(--muted);
        }}
        .field-acc {{
            font-weight: 600;
        }}
        /* Strategy Metal Matrix */
        .matrix-section {{
            background: var(--card-bg);
            border-radius: 18px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }}
        .matrix-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .matrix-table th, .matrix-table td {{
            padding: 0.75rem 1rem;
            text-align: center;
        }}
        .matrix-table th:first-child, .matrix-table td:first-child {{
            text-align: left;
        }}
        .matrix-table th {{
            background: var(--surface);
            font-weight: 600;
        }}
        .strategy-name {{
            font-weight: 500;
        }}
        .matrix-acc {{
            padding: 0.3rem 0.6rem;
            border-radius: 6px;
            font-weight: 600;
            font-size: 0.9rem;
        }}
        /* Hybrid Analysis Section */
        .hybrid-section {{
            background: var(--card-bg);
            border-radius: 18px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }}
        .hybrid-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .hybrid-table th, .hybrid-table td {{
            padding: 0.75rem 1rem;
        }}
        .hybrid-table th {{
            background: var(--surface);
            text-align: left;
        }}
        .combo-names {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        .combo-plus {{
            color: var(--muted);
            font-size: 0.8rem;
        }}
        .acc-value {{
            font-weight: 600;
        }}
        .improvement {{
            font-weight: 700;
        }}
        .hybrid-note {{
            color: var(--muted);
            font-size: 0.85rem;
            margin-top: 1rem;
            padding: 0.75rem;
            background: rgba(255,255,255,0.02);
            border-radius: 10px;
        }}
        footer {{ text-align: center; color: var(--muted); margin-top: 3rem; font-size: 0.85rem; }}
        @media (max-width: 600px) {{
            body {{ padding: 1rem; }}
            .strategy-grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <main class="container">
        <header class="hero">
            <h1>🔬 xScanner Strategy Benchmark</h1>
            <p class="meta">Generated on {created_at}</p>
            <p>{summary_text}</p>
        </header>
        {exec_summary}
        {strategy_metal_matrix}
        {metal_accuracy_section}
        {hybrid_analysis}
        <section>
            <h2>Performance Summary: Accuracy vs. Speed</h2>
            {summary_chart}
        </section>
        <section>
            <h2>Strategy League Table</h2>
            <table>
                {aggregate_rows}
            </table>
        </section>
        {image_sections}
    </main>
    <footer>
        Bullion Bar Recognition &mdash; Automated report generated from reports/strategy_benchmark_results.json
    </footer>
    <script>
        document.addEventListener('DOMContentLoaded', () => {{
            document.querySelectorAll('.toggle-btn').forEach(btn => {{
                btn.addEventListener('click', () => {{
                    const targetId = btn.getAttribute('data-target');
                    const panel = targetId ? document.getElementById(targetId) : null;
                    if (!panel) return;
                    panel.classList.toggle('is-open');
                    btn.classList.toggle('is-active');
                }});
            }});
        }});
    </script>
</body>
</html>
"""
