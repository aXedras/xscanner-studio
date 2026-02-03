"""HTML template for order compare report."""

ORDER_COMPARE_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>Order Compare Report</title>
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
      --warn: #ffa726;
      --border: rgba(255,255,255,0.08);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: linear-gradient(130deg, #050910, #101b33);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
      color: var(--text);
      line-height: 1.45;
      padding: 2rem;
    }}
    .container {{ max-width: 1400px; margin: 0 auto; }}
    header.hero {{
      background: var(--card-bg);
      padding: 1.5rem 1.75rem;
      border-radius: 18px;
      box-shadow: 0 25px 60px rgba(5, 10, 20, 0.45);
      border: 1px solid rgba(255, 255, 255, 0.05);
      margin-bottom: 1.5rem;
    }}
    h1 {{ margin: 0 0 0.25rem 0; font-size: 1.8rem; }}
    .meta {{ color: var(--muted); font-size: 0.9rem; }}

    .card {{
      background: var(--card-bg);
      border-radius: 18px;
      border: 1px solid rgba(255, 255, 255, 0.05);
      padding: 1.25rem;
      margin-bottom: 1.5rem;
    }}

    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ padding: 0.75rem 0.75rem; text-align: left; vertical-align: top; }}
    th {{ background: var(--surface); position: sticky; top: 0; z-index: 1; }}
    tr td {{ border-top: 1px solid rgba(255,255,255,0.06); }}
    .muted {{ color: var(--muted); }}

    .meta-row {{
      min-height: 1.35rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;
      flex-wrap: nowrap;
      overflow: hidden;
      white-space: nowrap;
      color: var(--muted);
    }}
    .meta-k {{ font-size: 0.78rem; opacity: 0.9; }}
    .meta-v {{
      font-size: 0.78rem;
      padding: 0.05rem 0.35rem;
      border: 1px solid rgba(255,255,255,0.14);
      border-radius: 8px;
      background: rgba(255,255,255,0.04);
      color: var(--muted);
      overflow: hidden;
      text-overflow: ellipsis;
      max-width: 100%;
    }}

    .th-wrap {{ display: flex; align-items: center; gap: 0.5rem; justify-content: space-between; }}
    .th-title {{ font-weight: 700; }}

    .badge {{
      display: inline-block;
      padding: 0.15rem 0.6rem;
      border-radius: 999px;
      font-size: 0.75rem;
      border: 1px solid var(--border);
      background: rgba(255,255,255,0.06);
    }}
    .badge.ok {{ border-color: rgba(69,196,134,0.35); background: rgba(69,196,134,0.15); color: var(--success); }}
    .badge.err {{ border-color: rgba(255,95,109,0.35); background: rgba(255,95,109,0.15); color: var(--error); }}
    .badge.warn {{ border-color: rgba(255,167,38,0.35); background: rgba(255,167,38,0.14); color: var(--warn); }}

    .cell-top {{ display: flex; gap: 0.5rem; flex-wrap: wrap; align-items: center; }}
    .cell-title {{ font-weight: 650; }}

    .btn {{
      cursor: pointer;
      border-radius: 999px;
      border: 1px solid rgba(74, 212, 255, 0.4);
      background: rgba(74, 212, 255, 0.15);
      color: var(--text);
      font-size: 0.8rem;
      padding: 0.25rem 0.7rem;
    }}
    .btn.subtle {{ border-color: rgba(255,255,255,0.14); background: rgba(255,255,255,0.06); }}
    .btn.tiny {{ font-size: 0.75rem; padding: 0.18rem 0.55rem; }}

    .panel {{
      display: none;
      margin-top: 0.6rem;
      padding: 0.75rem;
      border-radius: 12px;
      background: rgba(255,255,255,0.04);
      border: 1px solid rgba(255,255,255,0.06);
    }}
    .panel.open {{ display: block; }}
    pre {{ margin: 0; white-space: pre-wrap; word-break: break-word; font-size: 0.8rem; color: var(--muted); }}

    .grid {{ display: grid; grid-template-columns: 1fr; gap: 0.8rem; }}

    .diff-summary {{ margin-top: 0.35rem; }}

    .diff-table-wrap {{ overflow: auto; border-radius: 12px; border: 1px solid rgba(255,255,255,0.06); }}
    .diff-table {{ width: 100%; border-collapse: collapse; font-size: 0.82rem; }}
    .diff-table th, .diff-table td {{ padding: 0.45rem 0.55rem; border-top: 1px solid rgba(255,255,255,0.06); vertical-align: top; }}
    .diff-table th {{ background: rgba(255,255,255,0.04); position: sticky; top: 0; z-index: 2; }}
    .diff-pre {{ margin: 0; white-space: pre-wrap; word-break: break-word; color: var(--muted); }}
    .diff-details summary {{ cursor: pointer; }}
    .diff-row.added .diff-right {{ background: rgba(69,196,134,0.10); }}
    .diff-row.removed .diff-left {{ background: rgba(255,95,109,0.10); }}
    .diff-row.changed .diff-left, .diff-row.changed .diff-right {{ background: rgba(255,167,38,0.06); }}

    /* Diff matrix (try to fit within viewport; no horizontal scroll). */
    .matrix-wrap {{ overflow: hidden; border-radius: 14px; border: 1px solid rgba(255,255,255,0.08); }}
    .matrix-container {{ display: none; }}
    .matrix-container.open {{ display: block; }}
    .matrix-table {{ width: 100%; table-layout: fixed; border-collapse: collapse; font-size: 0.75rem; }}
    .matrix-table th, .matrix-table td {{ padding: 0.35rem 0.4rem; border-top: 1px solid rgba(255,255,255,0.06); vertical-align: top; }}
    .matrix-table th {{ background: rgba(255,255,255,0.04); position: sticky; top: 0; z-index: 5; }}
    .matrix-field {{ position: sticky; left: 0; z-index: 6; background: rgba(17,27,47,0.98); width: 20%; }}
    .matrix-run {{ width: auto; }}
    .matrix-val {{ display: block; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: var(--muted); }}

    /* Raw text diff */
    .raw-compare {{ display: grid; grid-template-columns: 1fr; gap: 0.75rem; }}
    .raw-block {{ border: 1px solid rgba(255,255,255,0.06); border-radius: 12px; padding: 0.65rem 0.75rem; background: rgba(255,255,255,0.03); }}
    .raw-block > summary {{ cursor: pointer; list-style: none; }}
    .raw-block > summary::-webkit-details-marker {{ display:none; }}
    .raw-diff {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; font-size: 0.8rem; }}
    .raw-pre {{ margin: 0; max-height: 55vh; overflow: auto; white-space: pre-wrap; word-break: break-word; font-size: 0.8rem; color: var(--muted); }}
    .raw-diff {{ max-height: 55vh; overflow: auto; }}
    .rt-line {{ display:flex; gap: 0.5rem; padding: 0.1rem 0.35rem; border-radius: 8px; }}
    .rt-prefix {{ width: 1rem; opacity: 0.8; }}
    .rt-text {{ white-space: pre-wrap; word-break: break-word; }}
    .rt-add {{ background: rgba(69,196,134,0.10); }}
    .rt-del {{ background: rgba(255,95,109,0.10); }}
    .rt-same {{ background: rgba(255,255,255,0.02); }}
    .matrix-cell.ref {{ background: rgba(255,255,255,0.02); }}
    .matrix-cell.same {{ background: rgba(255,255,255,0.01); }}
    .matrix-cell.added {{ background: rgba(69,196,134,0.10); }}
    .matrix-cell.removed {{ background: rgba(255,95,109,0.10); }}
    .matrix-cell.changed {{ background: rgba(255,167,38,0.07); }}

    /* Global top input preview panel (does not shift page layout). */
    .top-preview {{
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      z-index: 50;
      background: rgba(11, 18, 33, 0.92);
      backdrop-filter: blur(10px);
      border-bottom: 1px solid rgba(255,255,255,0.10);
      box-shadow: 0 20px 50px rgba(0,0,0,0.45);
      display: none;
    }}
    .top-preview.open {{ display: block; }}
    .top-preview__inner {{ max-width: 1400px; margin: 0 auto; padding: 0.9rem 1.1rem; }}
    .top-preview__top {{ display: flex; justify-content: space-between; align-items: center; gap: 1rem; }}
    .top-preview__title {{ margin: 0; font-size: 1rem; }}
    .top-preview__meta {{ color: var(--muted); font-size: 0.85rem; }}
    .top-preview__body {{ margin-top: 0.75rem; max-height: 70vh; overflow: auto; }}
    .top-preview__links {{ margin-top: 0.5rem; display: flex; gap: 0.65rem; flex-wrap: wrap; }}
    .top-preview__frame {{ width: 100%; height: 60vh; min-height: 420px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.10); background: rgba(0,0,0,0.18); }}
    .top-preview__img {{ max-width: 100%; border-radius: 12px; border: 1px solid rgba(255,255,255,0.10); }}

    .kbd {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
      font-size: 0.8rem;
      padding: 0.05rem 0.4rem;
      border: 1px solid rgba(255,255,255,0.18);
      border-bottom-width: 2px;
      border-radius: 8px;
      color: var(--muted);
      background: rgba(255,255,255,0.06);
    }}
    a {{ color: var(--accent); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
  </style>
</head>
<body>
  <div id=\"top-preview\" class=\"top-preview\" aria-hidden=\"true\">
    <div class=\"top-preview__inner\">
      <div class=\"top-preview__top\">
        <div>
          <h2 id=\"top-preview-title\" class=\"top-preview__title\">Input Preview</h2>
          <div id=\"top-preview-meta\" class=\"top-preview__meta\">Tip: press <span class=\"kbd\">Esc</span> to close.</div>
        </div>
        <button id=\"top-preview-close\" class=\"btn\">Close</button>
      </div>
      <div class=\"top-preview__body\">
        <div id=\"top-preview-content\"></div>
        <div id=\"top-preview-links\" class=\"top-preview__links\"></div>
      </div>
    </div>
  </div>

  <div class=\"container\">
    <header class=\"hero\">
      <h1>Order Compare</h1>
      <div class=\"meta\">Base: <strong>{base}</strong> · Created at: {created_at} · Source dir: {root_dir}</div>
    </header>

    <section class=\"card\">
      <div class=\"muted\" style=\"margin-bottom: 0.75rem;\">All results shown on one row: baseline manual vs multiple cloud inputs.</div>
      {table_html}
    </section>

    <section class=\"card\">
      <div style=\"display:flex; justify-content: space-between; gap: 1rem; flex-wrap: wrap; align-items: baseline; margin-bottom: 0.75rem;\">
        <div style=\"display:flex; align-items: center; gap: 0.6rem;\">
          <div style=\"font-weight: 700;\">Diff Matrix</div>
          <button class=\"btn tiny subtle\" data-toggle=\"diff-matrix\">Show/Hide</button>
        </div>
        <div class=\"muted\">Columns = baseline + runs · Rows = fields with diffs. Values are compacted to fit.</div>
      </div>
      <div id=\"diff-matrix\" class=\"matrix-container open\">{matrix_html}</div>
    </section>

    <section class=\"card\">
      <div style=\"display:flex; justify-content: space-between; gap: 1rem; flex-wrap: wrap; align-items: baseline; margin-bottom: 0.75rem;\">
        <div style=\"font-weight: 700;\">Raw Text Compare</div>
        <div class=\"muted\">Baseline raw_text vs each run (highlighted).</div>
      </div>
      {raw_html}
    </section>
  </div>

  <script>
    const topPreview = document.getElementById('top-preview');
    const topPreviewTitle = document.getElementById('top-preview-title');
    const topPreviewMeta = document.getElementById('top-preview-meta');
    const topPreviewContent = document.getElementById('top-preview-content');
    const topPreviewLinks = document.getElementById('top-preview-links');
    const topPreviewClose = document.getElementById('top-preview-close');

    function openTopPreview(payloadJson) {{
      let payload;
      try {{
        payload = JSON.parse(payloadJson);
      }} catch (e) {{
        payload = {{ title: 'Input', files: [] }};
      }}

      const title = payload.title || 'Input';
      const files = Array.isArray(payload.files) ? payload.files : [];

      topPreviewTitle.textContent = title;
      topPreviewMeta.textContent = files.length ? (files.length + ' file(s)') : 'No files';
      topPreviewContent.innerHTML = '';
      topPreviewLinks.innerHTML = '';

      function renderFile(file) {{
        topPreviewContent.innerHTML = '';
        if (!file || !file.url) {{
          topPreviewContent.innerHTML = '<div class="muted">Missing file</div>';
          return;
        }}
        if (file.type === 'pdf') {{
          const iframe = document.createElement('iframe');
          iframe.className = 'top-preview__frame';
          iframe.src = file.url;
          topPreviewContent.appendChild(iframe);
          return;
        }}
        if (file.type === 'image') {{
          const img = document.createElement('img');
          img.className = 'top-preview__img';
          img.src = file.url;
          img.alt = file.name || 'image';
          topPreviewContent.appendChild(img);
          return;
        }}
        topPreviewContent.innerHTML = '<div class="muted">Preview not supported</div>';
      }}

      files.forEach((f, idx) => {{
        const a = document.createElement('a');
        a.href = f.url || '#';
        a.target = '_blank';
        a.rel = 'noreferrer';
        a.textContent = f.name || ('file ' + (idx + 1));
        a.addEventListener('click', (ev) => {{
          // If user wants preview switching, prevent navigation.
          ev.preventDefault();
          renderFile(f);
        }});
        topPreviewLinks.appendChild(a);
      }});

      if (files.length) {{
        renderFile(files[0]);
      }}

      topPreview.classList.add('open');
      topPreview.setAttribute('aria-hidden', 'false');
      window.scrollTo({{ top: 0, behavior: 'smooth' }});
    }}

    function closeTopPreview() {{
      topPreview.classList.remove('open');
      topPreview.setAttribute('aria-hidden', 'true');
      topPreviewContent.innerHTML = '';
      topPreviewLinks.innerHTML = '';
    }}

    topPreviewClose.addEventListener('click', closeTopPreview);
    document.addEventListener('keydown', (e) => {{
      if (e.key === 'Escape') closeTopPreview();
    }});

    document.addEventListener('click', (e) => {{
      const btn = e.target.closest('[data-toggle]');
      if (btn) {{
        const id = btn.getAttribute('data-toggle');
        const el = document.getElementById(id);
        if (el) el.classList.toggle('open');
        return;
      }}

      const inputBtn = e.target.closest('[data-input]');
      if (!inputBtn) return;
      const payloadJson = inputBtn.getAttribute('data-input');
      if (!payloadJson) return;
      openTopPreview(payloadJson);
    }});
  </script>
</body>
</html>
"""
