from __future__ import annotations

from types import SimpleNamespace

from xscanner.server.config import reload_config
from xscanner.server.order.ai.vision_mock import VisionMarkerTextMock, vision_marker_text_mock
from xscanner.server.order.service import OrderExtractionService
from xscanner.server.order.strategy import OrderStrategyChoice


def test_order_service_aggregates_multiple_llm_calls_and_costs(monkeypatch) -> None:
    service = OrderExtractionService()

    def fake_extract_text_from_pdf_bytes(_: bytes) -> str:
        # Must be "good" according to text_quality_gate.
        anchors = "\n".join(
            [
                "INVOICE / ORDER CONFIRMATION",
                "ORDER DATE",
                "VALUE DATE",
                "UNIT PRICE",
                "TOTAL",
                "SUB TOTAL",
                "ITEM",
                "QUANTITY",
                "$",
            ]
        )
        return (anchors + "\n") * 120

    def fake_render_pdf_pages_to_png_bytes(_: bytes) -> list[bytes]:
        return [b"png-bytes-1", b"png-bytes-2"]

    def fake_finalize_order_extraction(*_, **__) -> tuple[SimpleNamespace, dict]:
        finalized = SimpleNamespace(
            extracted_data={
                "document": {
                    "document_issuer": "ACME",
                    "document_type": "invoice",
                    "document_number": "INV-1",
                    "document_date": "2026-01-01",
                },
                "parties": {},
                "order_terms": {},
                "order_items": [],
            }
        )
        raw_debug = {"raw_tables": [], "raw_kv": []}
        return finalized, raw_debug

    def fake_get_order_strategy(_: OrderStrategyChoice):
        class FakeImpl:
            name = "fake"

            def __init__(self) -> None:
                self.calls = 0

            def extract_from_text(
                self,
                _raw_text: str,
                *,
                raw=None,
                issuer_hint: str | None = None,
                trace=None,
            ):
                _ = raw
                _ = issuer_hint
                self.calls += 1

                if trace is not None:
                    # Simulate one AI call per strategy run.
                    if self.calls == 1:
                        usage = {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15}
                    else:
                        usage = {"input_tokens": 20, "output_tokens": 10, "total_tokens": 30}

                    with trace.span(
                        "cloud.ai_extract",
                        attrs={
                            "provider": "openai",
                            "model": "gpt-5.2",
                            "usage": usage,
                        },
                    ):
                        pass

                parsed_items = [] if self.calls == 1 else [SimpleNamespace()]
                ai_meta = None
                if self.calls == 1:
                    # Force semantic fallback.
                    ai_meta = {
                        "confidence": {"order_items": 0.2},
                        "readiness": {"reconciliation_ready": False},
                        "warnings": ["order_items missing"],
                    }

                return SimpleNamespace(
                    success=True,
                    parsed=SimpleNamespace(items=parsed_items),
                    strategy_used="order/cloud",
                    error=None,
                    issuer="ACME",
                    doc_type="invoice",
                    doc_type_candidates=["invoice"],
                    raw=None,
                    input_mode="text",
                    debug_marker_text=None,
                    debug_normalized_text=None,
                    ai_meta=ai_meta,
                )

        return FakeImpl()

    # Configure pricing via env vars (OpenAI only).
    monkeypatch.setenv("OPENAI_PRICE_INPUT_PER_1M_USD", "1.0")
    monkeypatch.setenv("OPENAI_PRICE_OUTPUT_PER_1M_USD", "2.0")
    reload_config()

    monkeypatch.setattr(
        "xscanner.server.order.workflow.textify.extract_text_from_pdf_bytes",
        fake_extract_text_from_pdf_bytes,
    )
    monkeypatch.setattr(
        "xscanner.server.order.workflow.textify.render_pdf_pages_to_png_bytes",
        fake_render_pdf_pages_to_png_bytes,
    )
    monkeypatch.setattr(
        "xscanner.server.order.workflow.fallback.render_pdf_pages_to_png_bytes",
        fake_render_pdf_pages_to_png_bytes,
    )
    monkeypatch.setattr(
        "xscanner.server.order.service.finalize_order_extraction",
        fake_finalize_order_extraction,
    )
    monkeypatch.setattr(
        "xscanner.server.order.service.get_order_strategy",
        fake_get_order_strategy,
    )

    vision_mock = VisionMarkerTextMock(
        marker_text="__DOCUMENT__\nDOCUMENT ISSUER: ACME\n",
        provider="openai",
        model="gpt-5.2",
        usage={"input_tokens": 7, "output_tokens": 3, "total_tokens": 10},
    )

    with vision_marker_text_mock(vision_mock):
        res = service.extract(pdf_bytes=b"%PDF-1.7\n...", strategy=OrderStrategyChoice.cloud)

    assert res.success is True

    # Expect 3 calls: cloud (attempt=1), vision marker-text (attempt=2), cloud (attempt=2)
    assert len(res.result.meta.llm_calls) == 3

    ops = [(c.operation, c.attempt) for c in res.result.meta.llm_calls]
    assert ("cloud.ai_extract", 1) in ops
    assert ("input.textify", 2) in ops
    assert ("cloud.ai_extract", 2) in ops

    # Totals should sum token counts.
    assert res.result.meta.llm_usage is not None
    assert res.result.meta.llm_usage.input_tokens == 10 + 7 + 20
    assert res.result.meta.llm_usage.output_tokens == 5 + 3 + 10
    assert res.result.meta.llm_usage.total_tokens == 15 + 10 + 30

    # And sum costs (USD per 1M tokens):
    # (10/1e6*1 + 5/1e6*2) + (7/1e6*1 + 3/1e6*2) + (20/1e6*1 + 10/1e6*2)
    expected_cost = (10 / 1_000_000.0) * 1.0 + (5 / 1_000_000.0) * 2.0
    expected_cost += (7 / 1_000_000.0) * 1.0 + (3 / 1_000_000.0) * 2.0
    expected_cost += (20 / 1_000_000.0) * 1.0 + (10 / 1_000_000.0) * 2.0

    assert res.result.meta.llm_usage.cost_usd is not None
    assert abs(float(res.result.meta.llm_usage.cost_usd) - expected_cost) < 1e-12
