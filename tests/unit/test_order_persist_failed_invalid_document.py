from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

import pytest

from xscanner.lib.trace_tree import TraceTree
from xscanner.server.order.http_routes.persistence_flow import (
    maybe_persist,
    maybe_persist_failed_run,
)
from xscanner.server.order.http_routes.types import ExtractionRun
from xscanner.server.order.models import OrderExtractResponse
from xscanner.server.order.types import InvalidOrderDocument, ParsedOrder


@pytest.mark.asyncio
async def test_failed_invalid_order_document_is_persisted_for_review(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    persisted_order_id = uuid4()

    async def fake_persist_order_pdf_to_supabase(**kwargs):  # type: ignore[no-untyped-def]
        assert kwargs.get("document_issuer") == "unknown"
        assert kwargs.get("document_type") == "invoice"
        assert str(kwargs.get("document_number") or "").startswith("error-sha256:")
        assert kwargs.get("document_date") == date(1970, 1, 1)
        assert kwargs.get("error") == "Missing document_number"

        from xscanner.server.order.persistence import PersistedOrder

        return PersistedOrder(
            order_id=UUID(str(persisted_order_id)),
            original_id=UUID(str(persisted_order_id)),
            storage_path="orders/x/y.pdf",
        )

    import xscanner.server.order.http_routes.persistence_flow as persistence_http

    monkeypatch.setattr(
        persistence_http,
        "persist_order_pdf_to_supabase",
        fake_persist_order_pdf_to_supabase,
    )

    trace = TraceTree.start(name="order.process")
    trace.finish_error(error=InvalidOrderDocument("Missing document_number"))

    run = ExtractionRun(
        success=False,
        request_id="req-1",
        pdf_bytes=b"%PDF-1.4 fake",
        filename="x.pdf",
        parsed=None,
        result={},
        persisted_extracted_data={},
        trace_tree=trace,
        processing_time=0.1,
        strategy_used="order/manual",
        error="Missing document_number",
    )

    response = OrderExtractResponse(
        success=False,
        request_id="req-1",
        order_id=None,
        result={},
        processing_time=0.1,
        strategy_used="order/manual",
        error="Missing document_number",
    )

    err = await maybe_persist_failed_run(run=run, response=response)
    assert err is None
    assert response.order_id == str(persisted_order_id)


@pytest.mark.asyncio
async def test_invalid_order_document_in_child_span_is_detected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    persisted_order_id = uuid4()

    async def fake_persist_order_pdf_to_supabase(**kwargs):  # type: ignore[no-untyped-def]
        from xscanner.server.order.persistence import PersistedOrder

        return PersistedOrder(
            order_id=UUID(str(persisted_order_id)),
            original_id=UUID(str(persisted_order_id)),
            storage_path="orders/x/y.pdf",
        )

    import xscanner.server.order.http_routes.persistence_flow as persistence_http

    monkeypatch.setattr(
        persistence_http,
        "persist_order_pdf_to_supabase",
        fake_persist_order_pdf_to_supabase,
    )

    trace = TraceTree.start(name="order.process")
    try:
        with trace.span("markers.ensure_doc_id"):
            raise InvalidOrderDocument("Missing document_number")
    except InvalidOrderDocument:
        # Simulates higher-level catching without calling trace.finish_error.
        pass

    run = ExtractionRun(
        success=False,
        request_id="req-2",
        pdf_bytes=b"%PDF-1.4 fake",
        filename="x.pdf",
        parsed=None,
        result={},
        persisted_extracted_data={},
        trace_tree=trace,
        processing_time=0.1,
        strategy_used="order/manual",
        error="Missing document_number",
    )

    response = OrderExtractResponse(
        success=False,
        request_id="req-2",
        order_id=None,
        result={},
        processing_time=0.1,
        strategy_used="order/manual",
        error="Missing document_number",
    )

    err = await maybe_persist_failed_run(run=run, response=response)
    assert err is None
    assert response.order_id == str(persisted_order_id)


@pytest.mark.asyncio
async def test_unknown_issuer_is_persisted_as_error(monkeypatch: pytest.MonkeyPatch) -> None:
    persisted_order_id = uuid4()

    async def fake_persist_order_pdf_to_supabase(**kwargs):  # type: ignore[no-untyped-def]
        assert kwargs.get("document_issuer") == "unknown"
        assert str(kwargs.get("document_number") or "").startswith("error-sha256:")
        assert kwargs.get("document_date") == date(1970, 1, 1)
        assert kwargs.get("error") == "unknown_document_issuer"

        from xscanner.server.order.persistence import PersistedOrder

        return PersistedOrder(
            order_id=UUID(str(persisted_order_id)),
            original_id=UUID(str(persisted_order_id)),
            storage_path="orders/x/y.pdf",
        )

    import xscanner.server.order.http_routes.persistence_flow as persistence_http

    monkeypatch.setattr(
        persistence_http,
        "persist_order_pdf_to_supabase",
        fake_persist_order_pdf_to_supabase,
    )

    run = ExtractionRun(
        success=True,
        request_id="req-unknown",
        pdf_bytes=b"%PDF-1.4 fake",
        filename="x.pdf",
        parsed=ParsedOrder(
            document_issuer="unknown",
            document_type="invoice",
            document_number="INV-123",
            document_date=date(2026, 2, 2),
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
            raw_text="",
            extracted_data={},
            items=[],
        ),
        result={},
        persisted_extracted_data={"meta": {"confidence": {"overall": 0.0}}},
        trace_tree=None,
        processing_time=0.1,
        strategy_used="order/cloud",
        error=None,
    )

    response = OrderExtractResponse(
        success=True,
        request_id="req-unknown",
        order_id=None,
        result={},
        processing_time=0.1,
        strategy_used="order/cloud",
        error=None,
    )

    err = await maybe_persist(run=run, response=response)
    assert err is None
    assert response.order_id == str(persisted_order_id)


@pytest.mark.asyncio
async def test_processing_error_does_not_override_valid_document_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    persisted_order_id = uuid4()

    async def fake_persist_order_pdf_to_supabase(**kwargs):  # type: ignore[no-untyped-def]
        # Even if there are processing_error warnings, keep the real identity
        # and do not persist the DB row as `status=error`.
        assert kwargs.get("document_issuer") == "bank-julius-baer"
        assert kwargs.get("document_type") == "invoice"
        assert kwargs.get("document_number") == "ZPM.25312.00069.00"
        assert kwargs.get("document_date") == date(2025, 9, 24)
        assert kwargs.get("error") is None

        from xscanner.server.order.persistence import PersistedOrder

        return PersistedOrder(
            order_id=UUID(str(persisted_order_id)),
            original_id=UUID(str(persisted_order_id)),
            storage_path="orders/x/y.pdf",
        )

    import xscanner.server.order.http_routes.persistence_flow as persistence_http

    monkeypatch.setattr(
        persistence_http,
        "persist_order_pdf_to_supabase",
        fake_persist_order_pdf_to_supabase,
    )

    run = ExtractionRun(
        success=True,
        request_id="req-valid-id-error",
        pdf_bytes=b"%PDF-1.4 fake",
        filename="x.pdf",
        parsed=ParsedOrder(
            document_issuer="bank-julius-baer",
            document_type="invoice",
            document_number="ZPM.25312.00069.00",
            document_date=date(2025, 9, 24),
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
            raw_text="",
            extracted_data={},
            items=[],
        ),
        result={},
        persisted_extracted_data={"meta": {"warnings": ["processing_error=missing_order_items"]}},
        trace_tree=None,
        processing_time=0.1,
        strategy_used="order/manual",
        error=None,
    )

    response = OrderExtractResponse(
        success=True,
        request_id="req-valid-id-error",
        order_id=None,
        result={},
        processing_time=0.1,
        strategy_used="order/manual",
        error=None,
    )

    err = await maybe_persist(run=run, response=response)
    assert err is None
    assert response.order_id == str(persisted_order_id)
