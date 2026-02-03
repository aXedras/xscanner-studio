from __future__ import annotations

from xscanner.server.order.models import (
    OrderAmounts,
    OrderDocument,
    OrderExtractedData,
    OrderLineItem,
    OrderParties,
    OrderTerms,
)
from xscanner.server.order.workflow.order_confidence import (
    OrderConfidenceInputs,
    compute_confidence_and_readiness_with_debug,
)


def _structured_with_one_item(
    *, description: str | None, quantity: str | None
) -> OrderExtractedData:
    return OrderExtractedData(
        document=OrderDocument(
            document_issuer="a-mark",
            document_type="order_confirmation",
            document_number="720565",
            document_date="2025-09-03",
        ),
        parties=OrderParties(
            seller_name="A-Mark Precious Metals",
            buyer_name="BFI BULLION AG",
        ),
        order_terms=OrderTerms(currency="USD", amounts=OrderAmounts(total="135000.00")),
        order_items=[
            OrderLineItem(
                description=description,
                quantity=quantity,
            )
        ],
    )


def test_ai_meta_caps_order_items_confidence_and_blocks_readiness() -> None:
    structured = _structured_with_one_item(description="1 kg silver bar", quantity="100")

    inputs = OrderConfidenceInputs(
        structured=structured,
        raw_tables=[{"name": "order_items", "headers": ["QTY"], "rows": [["100"]]}],
        raw_kv=[],
        warnings=[],
        ai_meta={
            "confidence": {"order_items": 0.4, "document_identity": 1.0, "overall": 0.5},
            "readiness": {"reconciliation_ready": False, "reason": "items_ambiguous"},
            "warnings": [],
        },
    )

    confidence, readiness, debug = compute_confidence_and_readiness_with_debug(inputs)

    assert confidence.order_items == 0.4
    assert readiness.reconciliation_ready is False
    assert readiness.reason is not None
    assert "ai_meta_not_ready" in readiness.reason
    assert "items_ambiguous" in readiness.reason
    assert debug.ai_conf_order_items == 0.4
    assert debug.ai_ready is False


def test_ai_meta_does_not_increase_confidence() -> None:
    # Missing quantity makes the deterministic score pessimistic.
    structured = _structured_with_one_item(description="1 kg silver bar", quantity=None)

    inputs = OrderConfidenceInputs(
        structured=structured,
        raw_tables=[],
        raw_kv=[],
        warnings=[],
        ai_meta={
            "confidence": {"order_items": 0.9},
            "readiness": {"reconciliation_ready": True},
            "warnings": [],
        },
    )

    confidence, readiness, _debug = compute_confidence_and_readiness_with_debug(inputs)

    assert confidence.order_items == 0.0
    assert readiness.reconciliation_ready is False


def test_ai_critical_warning_blocks_ready() -> None:
    structured = _structured_with_one_item(description="1 kg silver bar", quantity="100")

    inputs = OrderConfidenceInputs(
        structured=structured,
        raw_tables=[{"name": "order_items", "headers": ["QTY"], "rows": [["100"]]}],
        raw_kv=[],
        warnings=[],
        ai_meta={
            "warnings": ["CRITICAL: missing/ambiguous order items"],
        },
    )

    _confidence, readiness, debug = compute_confidence_and_readiness_with_debug(inputs)

    assert "critical_warnings_present" in (readiness.reason or "")
    assert debug.critical_warnings
