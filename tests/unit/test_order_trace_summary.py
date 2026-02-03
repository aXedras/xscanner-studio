from __future__ import annotations

from xscanner.server.order.http_routes.helpers import format_trace_summary


def test_format_trace_summary_smoke_includes_key_fields() -> None:
    trace_root = {
        "type": "span",
        "name": "order.process",
        "status": "ok",
        "duration_ms": 1234.56,
        "attrs": {"strategy": "cloud", "issuer": "ACME"},
        "children": [
            {
                "type": "span",
                "name": "input.textify",
                "status": "ok",
                "duration_ms": 111.1,
                "attrs": {},
                "children": [],
            },
            {
                "type": "span",
                "name": "strategy.pipeline",
                "status": "ok",
                "duration_ms": 222.2,
                "attrs": {},
                "children": [],
            },
        ],
    }

    line = format_trace_summary(request_id="req-1", trace_root=trace_root)  # type: ignore[arg-type]

    assert "order.process summary" in line
    assert "request_id=req-1" in line
    assert "status=ok" in line
    assert "strategy=cloud" in line
    assert "issuer=ACME" in line
    assert "total_ms=1235" in line
    assert "textify_ms=111" in line
    assert "pipeline_ms=222" in line
    assert "llm_calls=" in line
