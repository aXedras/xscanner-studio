import json
from datetime import date
from uuid import uuid4

import httpx
import pytest

from xscanner.server.order.persistence import persist_order_pdf_to_supabase
from xscanner.server.persistence import close_supabase_client
from xscanner.server.supabase_rest import SupabaseRestClient, SupabaseRestConfig


@pytest.mark.asyncio
async def test_select_rows_and_order_persist_versioning(monkeypatch: pytest.MonkeyPatch):
    """Re-importing the same document identity should deactivate the previous row."""

    seen: list[tuple[str, str, dict[str, str], bytes]] = []

    # Simulate an existing active order for the identity.
    existing_order = {
        "id": str(uuid4()),
        "original_id": str(uuid4()),
        "storage_path": "orders/existing/existing.pdf",
        "extracted_data": {"meta": {"document_hash_sha256": "different"}},
    }

    async def handler(request: httpx.Request) -> httpx.Response:
        seen.append(
            (request.method, str(request.url), dict(request.headers), request.content or b"")
        )

        if request.url.path.startswith("/storage/v1/object/extractions/orders/"):
            return httpx.Response(200, json={"Key": request.url.path})

        if request.url.path == "/rest/v1/order" and request.method == "GET":
            # Two GETs are expected:
            # 1) Find active order by identity (select=id,original_id, limit=1)
            # 2) Load all order versions for original_id (select=id)
            select = request.url.params.get("select")
            if select == "id,original_id,storage_path,extracted_data":
                return httpx.Response(200, json=[existing_order])
            if select == "id":
                return httpx.Response(200, json=[{"id": existing_order["id"]}])
            return httpx.Response(400, json={"error": "unexpected select", "select": select})

        if request.url.path == "/rest/v1/order_item" and request.method == "PATCH":
            payload = json.loads(request.content.decode("utf-8"))
            assert payload["is_active"] is False
            assert "updated_by" not in payload
            return httpx.Response(200, json=[])

        if request.url.path == "/rest/v1/order" and request.method == "PATCH":
            payload = json.loads(request.content.decode("utf-8"))
            assert payload["is_active"] is False
            assert "updated_by" not in payload
            return httpx.Response(200, json=[existing_order])

        if request.url.path == "/rest/v1/order" and request.method == "POST":
            payload = json.loads(request.content.decode("utf-8"))
            assert payload["original_id"] == existing_order["original_id"]
            assert payload.get("updated_by") == "user_test_123"
            return httpx.Response(
                201, json=[{"id": payload["id"], "original_id": payload["original_id"]}]
            )

        if request.url.path == "/rest/v1/order_item" and request.method == "POST":
            payload = json.loads(request.content.decode("utf-8"))
            assert payload.get("updated_by") == "user_test_123"
            # If present in extracted items, serial_number must be persisted.
            if payload.get("description") == "1 kg Valcambi cast silver bar":
                assert payload.get("serial_number") == "AB 123 45"
            return httpx.Response(201, json=[{"id": payload["id"]}])

        return httpx.Response(404, json={"error": "not found"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http:
        client = SupabaseRestClient(
            SupabaseRestConfig(
                url="https://example.supabase.co",
                service_role_key="svc",
                storage_bucket="extractions",
            ),
            http_client=http,
        )

        # Monkeypatch the global client used by persistence.get_supabase_client()
        import xscanner.server.persistence as persistence

        persistence._supabase_client = client  # type: ignore[attr-defined]

        try:
            await persist_order_pdf_to_supabase(
                pdf_bytes=b"%PDF-1.4 fake",
                filename="x.pdf",
                document_issuer="a-mark",
                document_type="invoice",
                document_number="720565",
                document_date=date(2025, 9, 3),
                order_number="720565",
                order_date=date(2025, 9, 3),
                value_date=date(2025, 9, 12),
                shipping_date=date(2025, 9, 12),
                transaction_type="PHYSICAL",
                seller_name="A-Mark",
                buyer_name="BFI BULLION AG",
                currency="USD",
                shipping_charges_amount=0.0,
                other_charges_amount=None,
                subtotal_amount=None,
                total_amount=135000.0,
                strategy_used="pdf-text (a-mark)",
                confidence=None,
                processing_time=0.1,
                extracted_data={"document": {"document_issuer": "a-mark"}},
                updated_by="user_test_123",
                items=[
                    {
                        "item": "SBVALKGCAST",
                        "description": "1 kg Valcambi cast silver bar",
                        "quantity": "100",
                        "serial_number": "AB 123 45",
                        "metal": "silver",
                        "weight": "1",
                        "weight_unit": "kg",
                        "item_price": 1350.0,
                        "total_price": 135000.0,
                        "producer": "Valcambi",
                        "form": "bar",
                        "fineness": None,
                    }
                ],
                error=None,
            )
        finally:
            await close_supabase_client()

    # Expected: select existing, upload PDF, deactivate old, insert new order, insert item.
    methods = [m for m, *_ in seen]
    assert methods.count("GET") == 2
    assert methods.count("POST") >= 2
    assert methods.count("PATCH") == 2


@pytest.mark.asyncio
async def test_persist_order_creates_new_version_for_same_identity_and_pdf(
    monkeypatch: pytest.MonkeyPatch,
):
    """Uploading the same PDF again should still create a new order version (bitemporal)."""

    seen: list[tuple[str, str, dict[str, str], bytes]] = []

    pdf_bytes = b"%PDF-1.4 fake"
    import hashlib

    doc_hash = hashlib.sha256(pdf_bytes).hexdigest()
    existing_order = {
        "id": str(uuid4()),
        "original_id": str(uuid4()),
        "storage_path": "orders/existing/original.pdf",
        "extracted_data": {"meta": {"document_hash_sha256": doc_hash}},
    }

    async def handler(request: httpx.Request) -> httpx.Response:
        seen.append(
            (request.method, str(request.url), dict(request.headers), request.content or b"")
        )

        if request.url.path.startswith("/storage/v1/object/extractions/orders/"):
            return httpx.Response(200, json={"Key": request.url.path})

        if request.url.path == "/rest/v1/order" and request.method == "GET":
            select = request.url.params.get("select")
            if select == "id,original_id,storage_path,extracted_data":
                return httpx.Response(200, json=[existing_order])
            if select == "id":
                return httpx.Response(200, json=[{"id": existing_order["id"]}])
            return httpx.Response(400, json={"error": "unexpected select", "select": select})

        if request.url.path == "/rest/v1/order_item" and request.method == "PATCH":
            payload = json.loads(request.content.decode("utf-8"))
            assert payload["is_active"] is False
            assert "updated_by" not in payload
            return httpx.Response(200, json=[])

        if request.url.path == "/rest/v1/order" and request.method == "PATCH":
            payload = json.loads(request.content.decode("utf-8"))
            assert payload["is_active"] is False
            assert "updated_by" not in payload
            return httpx.Response(200, json=[existing_order])

        if request.url.path == "/rest/v1/order" and request.method == "POST":
            payload = json.loads(request.content.decode("utf-8"))
            assert payload["original_id"] == existing_order["original_id"]
            assert payload["storage_path"].startswith("orders/by-hash/")
            assert payload["storage_path"].endswith(f"{doc_hash}.pdf")
            assert payload.get("updated_by") == "user_test_456"
            return httpx.Response(
                201, json=[{"id": payload["id"], "original_id": payload["original_id"]}]
            )

        if request.url.path == "/rest/v1/order_item" and request.method == "POST":
            payload = json.loads(request.content.decode("utf-8"))
            assert payload.get("updated_by") == "user_test_456"
            return httpx.Response(201, json=[{"id": payload["id"]}])

        return httpx.Response(404, json={"error": "not found"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as http:
        client = SupabaseRestClient(
            SupabaseRestConfig(
                url="https://example.supabase.co",
                service_role_key="svc",
                storage_bucket="extractions",
            ),
            http_client=http,
        )

        import xscanner.server.persistence as persistence

        persistence._supabase_client = client  # type: ignore[attr-defined]

        try:
            persisted = await persist_order_pdf_to_supabase(
                pdf_bytes=pdf_bytes,
                filename="x.pdf",
                document_issuer="a-mark",
                document_type="invoice",
                document_number="720565",
                document_date=date(2025, 9, 3),
                order_number="720565",
                order_date=date(2025, 9, 3),
                value_date=date(2025, 9, 12),
                shipping_date=date(2025, 9, 12),
                transaction_type="PHYSICAL",
                seller_name="A-Mark",
                buyer_name="BFI BULLION AG",
                currency="USD",
                shipping_charges_amount=0.0,
                other_charges_amount=None,
                subtotal_amount=None,
                total_amount=135000.0,
                strategy_used="pdf-text (a-mark)",
                confidence=None,
                processing_time=0.1,
                extracted_data={"document": {"document_issuer": "a-mark"}},
                items=[],
                updated_by="user_test_456",
                error=None,
            )
            assert str(persisted.original_id) == existing_order["original_id"]
            assert str(persisted.order_id) != existing_order["id"]
            assert persisted.storage_path.endswith(f"{doc_hash}.pdf")
        finally:
            await close_supabase_client()

    methods = [m for m, *_ in seen]
    assert methods.count("GET") == 2
    assert methods.count("PATCH") == 2
    assert methods.count("POST") >= 2
