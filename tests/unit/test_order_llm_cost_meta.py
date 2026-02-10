from __future__ import annotations

from types import SimpleNamespace

from xscanner.server.config import reload_config
from xscanner.server.order.service import OrderExtractionService
from xscanner.server.order.strategy import OrderStrategyChoice


def test_order_service_sets_llm_usage_cost_usd_when_pricing_configured(monkeypatch) -> None:
    service = OrderExtractionService()

    def fake_extract_text_from_pdf_bytes(_: bytes) -> str:
        # Must be "good" according to text_quality_gate to prevent the service
        # from switching into the vision pre-pass during this unit test.
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
                if trace is not None:
                    with trace.span(
                        "cloud.ai_extract",
                        attrs={
                            "provider": "openai",
                            "model": "gpt-5.2",
                            "usage": {
                                "input_tokens": 1000,
                                "output_tokens": 500,
                                "total_tokens": 1500,
                            },
                        },
                    ):
                        pass
                return SimpleNamespace(
                    success=True,
                    parsed=SimpleNamespace(),
                    strategy_used="order/cloud",
                    error=None,
                    issuer="ACME",
                    doc_type="invoice",
                    doc_type_candidates=["invoice"],
                    raw=None,
                    input_mode="text",
                    debug_marker_text=None,
                    debug_normalized_text=None,
                )

        return FakeImpl()

    monkeypatch.setattr(
        "xscanner.server.order.workflow.textify.extract_text_from_pdf_bytes",
        fake_extract_text_from_pdf_bytes,
    )
    monkeypatch.setattr(
        "xscanner.server.order.service.finalize_order_extraction",
        fake_finalize_order_extraction,
    )
    monkeypatch.setattr(
        "xscanner.server.order.service.get_order_strategy",
        fake_get_order_strategy,
    )

    # Configure pricing via env vars (OpenAI only).
    monkeypatch.setenv("OPENAI_PRICE_INPUT_PER_1M_USD", "1.0")
    monkeypatch.setenv("OPENAI_PRICE_OUTPUT_PER_1M_USD", "2.0")
    reload_config()

    res = service.extract(pdf_bytes=b"%PDF-FAKE%", strategy=OrderStrategyChoice.cloud)

    assert res.success is True
    assert len(res.result.meta.llm_calls) == 1
    assert res.result.meta.llm_usage is not None
    assert res.result.meta.llm_usage.cost_usd is not None

    # Pricing is USD per 1M tokens.
    # cost = 1000/1e6*1.0 + 500/1e6*2.0 = 0.001 + 0.001 = 0.002
    assert abs(float(res.result.meta.llm_usage.cost_usd) - 0.002) < 1e-12

    assert res.result.meta.llm_calls[0].cost_usd is not None
    assert abs(float(res.result.meta.llm_calls[0].cost_usd) - 0.002) < 1e-12
