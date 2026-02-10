from __future__ import annotations

from types import SimpleNamespace

from xscanner.server.order.service import OrderExtractionService
from xscanner.server.order.strategy import OrderStrategyChoice


def test_order_service_sets_llm_usage_from_cloud_trace(monkeypatch) -> None:
    service = OrderExtractionService()

    def fake_extract_text_from_pdf_bytes(_: bytes) -> str:
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
                            "usage": {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15},
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

    res = service.extract(pdf_bytes=b"%PDF-FAKE%", strategy=OrderStrategyChoice.cloud)

    assert res.success is True
    assert hasattr(res.result, "meta")
    assert len(res.result.meta.llm_calls) == 1
    assert res.result.meta.llm_calls[0].operation == "cloud.ai_extract"
    assert res.result.meta.llm_calls[0].attempt == 1
    assert res.result.meta.llm_calls[0].provider == "openai"
    assert res.result.meta.llm_calls[0].model == "gpt-5.2"
    assert res.result.meta.llm_calls[0].input_tokens == 10
    assert res.result.meta.llm_calls[0].output_tokens == 5
    assert res.result.meta.llm_calls[0].total_tokens == 15

    assert res.result.meta.llm_usage is not None
    assert res.result.meta.llm_usage.provider == "openai"
    assert res.result.meta.llm_usage.model == "gpt-5.2"
    assert res.result.meta.llm_usage.input_tokens == 10
    assert res.result.meta.llm_usage.output_tokens == 5
    assert res.result.meta.llm_usage.total_tokens == 15


def test_order_service_leaves_llm_usage_none_without_cloud_trace(monkeypatch) -> None:
    service = OrderExtractionService()

    def fake_extract_text_from_pdf_bytes(_: bytes) -> str:
        return "dummy text"

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
                return SimpleNamespace(
                    success=True,
                    parsed=SimpleNamespace(),
                    strategy_used="order/manual",
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

    res = service.extract(pdf_bytes=b"%PDF-FAKE%", strategy=OrderStrategyChoice.manual)

    assert res.success is True
    assert hasattr(res.result, "meta")
    assert res.result.meta.llm_calls == []
    assert res.result.meta.llm_usage is None
