from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from types import SimpleNamespace

from xscanner.lib.trace_tree import iter_trace_spans
from xscanner.server.order.models import OrderExtractionConfidence, OrderExtractionReadiness
from xscanner.server.order.processing.raw_signals import RawOrderData
from xscanner.server.order.service import OrderExtractionService
from xscanner.server.order.strategy import OrderStrategyChoice
from xscanner.server.order.strategy.base import OrderParsingStrategy, OrderStrategyResult
from xscanner.server.order.types import ParsedOrder


def _span_names(trace_root: dict) -> list[str]:
    return [
        str(sp.get("name"))
        for sp in iter_trace_spans(trace_root)
        if sp.get("type") == "span" and isinstance(sp.get("name"), str)
    ]


def test_trace_runs_raw_signals_before_detect_initial(monkeypatch) -> None:
    @dataclass(frozen=True)
    class _FakeTextifyResult:
        success: bool
        raw_text: str | None
        effective_strategy: OrderStrategyChoice | None
        textify_mode: str | None
        strategy_used: str
        error: str | None = None

    raw_text = "ACME INVOICE\nTOTAL 10\n"

    def _fake_textify_input(*, pdf_bytes, page_images, strategy, trace):
        assert trace is not None
        return _FakeTextifyResult(
            success=True,
            raw_text=raw_text,
            effective_strategy=OrderStrategyChoice.manual,
            textify_mode="pdf_text",
            strategy_used="order/textify",
            error=None,
        )

    called: dict[str, object] = {}

    class _FakeStrategy(OrderParsingStrategy):
        @property
        def name(self) -> str:
            return "order/fake"

        def extract_from_text(
            self,
            raw_text_arg: str,
            *,
            raw: RawOrderData | None = None,
            issuer_hint: str | None = None,
            trace=None,
        ) -> OrderStrategyResult:
            called["raw_text"] = raw_text_arg
            called["raw"] = raw
            called["issuer_hint"] = issuer_hint

            extracted_data = {
                "document": {
                    "document_issuer": "ACME",
                    "document_type": "invoice",
                    "document_number": "INV-1",
                    "document_date": "2026-01-01",
                },
                "parties": {
                    "seller_name": None,
                    "buyer_name": None,
                    "shipping_from": None,
                    "shipping_to": None,
                },
                "order_terms": {
                    "currency": None,
                    "order_date": None,
                    "order_number": None,
                    "shipping_date": None,
                    "value_date": None,
                    "transaction_type": None,
                    "amounts": {
                        "subtotal": None,
                        "shipping_charges": None,
                        "other_charges": None,
                        "total": None,
                    },
                },
                "order_items": [],
            }
            parsed = ParsedOrder(
                document_issuer="ACME",
                document_type="invoice",
                document_number="INV-1",
                document_date=date(2026, 1, 1),
                order_number=None,
                order_date=None,
                value_date=None,
                shipping_date=None,
                transaction_type=None,
                seller_name=None,
                buyer_name=None,
                currency=None,
                subtotal_amount=None,
                shipping_charges_amount=None,
                other_charges_amount=None,
                total_amount=None,
                raw_text=raw_text_arg,
                extracted_data=extracted_data,
                items=[],
            )

            return OrderStrategyResult(
                parsed=parsed,
                issuer="ACME",
                doc_type="invoice",
                doc_type_candidates=["invoice"],
                raw=raw,
                strategy_used=self.name,
                error=None,
                input_mode="text",
            )

    def _fake_compute_confidence_and_readiness_with_debug(_):
        return (
            OrderExtractionConfidence(
                document_identity=1.0,
                order_items=0.0,
                overall=1.0,
            ),
            OrderExtractionReadiness(reconciliation_ready=True, reason="ok"),
            SimpleNamespace(
                order_items_threshold=0.0,
                order_items_has_table=False,
                order_items_bullion_score=0.0,
                ai_ready=True,
                warnings=[],
                critical_warnings=[],
            ),
        )

    def _fake_build_llm_meta(*, trace_root):
        return [], None

    def _fake_build_field_mapping_meta(
        *, structured_dict, strategy_used, result_field_mapping, trace_root
    ):
        return None

    import xscanner.server.order.service as service_module

    monkeypatch.setattr(service_module, "textify_input", _fake_textify_input)
    monkeypatch.setattr(service_module, "get_order_strategy", lambda _: _FakeStrategy())
    monkeypatch.setattr(
        service_module,
        "compute_confidence_and_readiness_with_debug",
        _fake_compute_confidence_and_readiness_with_debug,
    )
    monkeypatch.setattr(service_module, "build_llm_meta", _fake_build_llm_meta)
    monkeypatch.setattr(service_module, "build_field_mapping_meta", _fake_build_field_mapping_meta)
    monkeypatch.setattr(service_module, "get_provider_by_issuer", lambda _: None)

    svc = OrderExtractionService()
    res = svc.extract(
        page_images=[b"fake"],
        strategy=OrderStrategyChoice.manual,
        debug=False,
        serial_number_expected=False,
    )

    assert res.success is True
    names = _span_names(res.trace.root)

    raw_idx = names.index("raw_signals.extract")
    detect_idx = names.index("detect.initial")
    strat_idx = names.index("strategy.extract_from_text")

    assert raw_idx < detect_idx < strat_idx

    assert called["raw_text"] == raw_text
    assert isinstance(called.get("issuer_hint"), str)
    assert isinstance(called.get("raw"), RawOrderData)
