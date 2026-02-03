from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from xscanner.mockdata.order_extract import (
    build_order_extract_mock_name_from_upload_filename,
    get_order_extract_mock_path,
)
from xscanner.mockdata.order_vision import (
    build_order_vision_mock_name_from_upload_filename,
    get_order_vision_mock_path,
)
from xscanner.server.config import reload_config
from xscanner.server.server import app


@pytest.mark.integration
def test_order_extract_upload_parses_sample_pdf_without_persistence(
    monkeypatch: pytest.MonkeyPatch,
):
    """Smoke-test the PDF order ingestion endpoint.

    This test uses the repository sample PDF and asserts that the endpoint can:
    - parse text from the PDF
    - extract a strict document identity
    - return a stable canonical shape

    Persistence is intentionally disabled for this integration test.
    """

    # Ensure Supabase persistence is disabled for this test run.
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    # Ensure config is reloaded from the patched environment (lifespan also does this,
    # but only when the TestClient is used as a context manager).
    reload_config()
    import xscanner.server.persistence as persistence

    persistence._supabase_client = None  # type: ignore[attr-defined]

    pdf_path = Path(__file__).resolve().parents[2] / "invoices" / "72056547.pdf"
    assert pdf_path.exists(), f"Missing sample PDF at {pdf_path}"

    with TestClient(app) as client:
        with pdf_path.open("rb") as f:
            response_public = client.post(
                "/order/extract/upload",
                files={"file": ("72056547.pdf", f, "application/pdf")},
            )

        with pdf_path.open("rb") as f:
            response_debug = client.post(
                "/order/extract/upload",
                params={"debug": "true"},
                files={"file": ("72056547.pdf", f, "application/pdf")},
            )

    assert response_public.status_code == 200
    payload = response_public.json()

    assert payload["success"] is True
    assert payload["order_id"] is None
    assert payload["error"] is None

    result = payload["result"]
    assert isinstance(result, dict)

    structured = result.get("structured_data")
    assert isinstance(structured, dict)

    document = structured.get("document")
    assert isinstance(document, dict)

    assert document.get("document_issuer") == "a-mark"
    assert document.get("document_type") in {"invoice", "order_confirmation", "delivery_note"}
    assert isinstance(document.get("document_number"), str)
    assert isinstance(document.get("document_date"), str)

    parties = structured.get("parties")
    assert isinstance(parties, dict)
    assert "shipping_from" in parties
    assert "shipping_to" in parties
    assert parties.get("shipping_from")
    assert "LOOMIS" in str(parties.get("shipping_from")).upper()

    assert parties.get("buyer_name")
    assert parties.get("shipping_to") == parties.get("buyer_name")

    order_terms = structured.get("order_terms")
    assert isinstance(order_terms, dict)
    amounts = order_terms.get("amounts")
    assert isinstance(amounts, dict)
    assert "total" in amounts
    assert amounts.get("subtotal")
    assert "amounts" not in structured

    order_items = structured.get("order_items")
    assert isinstance(order_items, list)
    assert len(order_items) >= 1

    # Public endpoint must not include raw debug signals.
    assert result.get("raw") is None

    # Debug endpoint includes raw.* for internal use.
    assert response_debug.status_code == 200
    payload_debug = response_debug.json()
    debug_result = payload_debug["result"]
    assert isinstance(debug_result, dict)

    raw = debug_result.get("raw")
    assert isinstance(raw, dict)
    raw_kv = raw.get("raw_kv")
    assert isinstance(raw_kv, list)

    raw_tables = raw.get("raw_tables")
    assert isinstance(raw_tables, list)
    order_items_table = next(
        (t for t in raw_tables if isinstance(t, dict) and t.get("name") == "order_items"), None
    )
    assert isinstance(order_items_table, dict)
    assert isinstance(order_items_table.get("headers"), list)
    assert isinstance(order_items_table.get("rows"), list)
    assert len(order_items_table.get("rows")) >= 1

    # We expect best-effort key/value capture for amounts.
    assert any(kv.get("key_normalized") == "sub_total" for kv in raw_kv)
    assert any(kv.get("key_normalized") == "total" for kv in raw_kv)

    # Derived normalization signals
    assert any(kv.get("key") == "documentIssuer" for kv in raw_kv)
    assert any(kv.get("key") == "documentType" for kv in raw_kv)
    assert any(kv.get("key") == "documentNumber" for kv in raw_kv)
    assert any(kv.get("key") == "documentDate" for kv in raw_kv)
    assert any(kv.get("key") == "receiver" for kv in raw_kv)

    # The identity signals should be at the very top for easy routing.
    assert raw_kv[0].get("key") == "documentIssuer"
    assert raw_kv[1].get("key") == "documentType"

    first = order_items[0]
    assert isinstance(first, dict)
    assert "item" in first
    assert "description" in first
    assert "item_price" in first
    assert "total_price" in first
    assert "metal" in first
    assert "weight" in first
    assert "weight_unit" in first
    assert "producer" in first
    assert "form" in first
    assert "fineness" in first

    assert first.get("item_price") is not None
    assert first.get("total_price") is not None


@pytest.mark.integration
def test_order_extract_upload_cloud_mock_works_without_openai_key(
    monkeypatch: pytest.MonkeyPatch,
):
    """Integration-test mock mode for cloud strategy.

    Goal: allow exercising the endpoint with `strategy=cloud` in CI/dev without
    external API calls or API keys.
    """

    # Ensure external dependencies are disabled for this test run.
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    reload_config()
    import xscanner.server.persistence as persistence

    persistence._supabase_client = None  # type: ignore[attr-defined]

    pdf_path = Path(__file__).resolve().parents[2] / "invoices" / "72056547.pdf"
    assert pdf_path.exists(), f"Missing sample PDF at {pdf_path}"

    expected_mock_name = build_order_extract_mock_name_from_upload_filename(
        upload_filename="72056547.pdf"
    )
    has_fixture = get_order_extract_mock_path(expected_mock_name).exists()

    with TestClient(app) as client:
        with pdf_path.open("rb") as f:
            response = client.post(
                "/order/extract/upload",
                params={"strategy": "cloud", "use_mock": "true"},
                files={"file": ("72056547.pdf", f, "application/pdf")},
            )

    assert response.status_code == 200
    payload = response.json()

    # If no recorded fixture exists, mock mode should fail explicitly.
    if not has_fixture:
        assert payload["success"] is False
        assert isinstance(payload.get("error"), str)
        assert expected_mock_name in payload["error"]
        return

    assert payload["success"] is True
    assert payload["error"] is None
    assert "mock" in str(payload.get("strategy_used") or "").lower()

    result = payload["result"]
    structured = result.get("structured_data")
    assert isinstance(structured, dict)
    assert isinstance(structured.get("order_items"), list)

    meta = result.get("meta")
    assert isinstance(meta, dict)
    assert meta.get("strategy") == "cloud"


@pytest.mark.integration
def test_order_extract_upload_cloud_mock_uses_recorded_ai_response_when_present(
    monkeypatch: pytest.MonkeyPatch,
):
    """If a recorded AI mock exists, cloud mock should exercise cloud pipeline.

    We prove this by requesting debug output and asserting the trace contains
    the cloud extraction step with provider=mock.
    """

    pdf_path = Path(__file__).resolve().parents[2] / "invoices" / "72056547.pdf"
    assert pdf_path.exists(), f"Missing sample PDF at {pdf_path}"

    mock_name = build_order_extract_mock_name_from_upload_filename(upload_filename="72056547.pdf")
    if not get_order_extract_mock_path(mock_name).exists():
        pytest.skip(
            "Recorded extract mock fixture not present; run `make record-order-extract-mock FILE=invoices/72056547.pdf` to record it"
        )

    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    reload_config()
    import xscanner.server.persistence as persistence

    persistence._supabase_client = None  # type: ignore[attr-defined]

    with TestClient(app) as client:
        with pdf_path.open("rb") as f:
            response = client.post(
                "/order/extract/upload",
                params={
                    "strategy": "cloud",
                    "use_mock": "true",
                    "debug": "true",
                },
                files={"file": ("72056547.pdf", f, "application/pdf")},
            )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True

    result = payload["result"]
    raw = result.get("raw")
    assert isinstance(raw, dict)
    trace = raw.get("trace")
    assert isinstance(trace, dict)

    def iter_spans(node: object):
        if not isinstance(node, dict):
            return
        if node.get("type") == "span":
            yield node
        for child in node.get("children") or []:
            yield from iter_spans(child)

    cloud_span = next(
        (sp for sp in iter_spans(trace) if sp.get("name") == "cloud.ai_extract"), None
    )
    assert isinstance(cloud_span, dict)
    attrs = cloud_span.get("attrs")
    assert isinstance(attrs, dict)
    assert attrs.get("provider") == "mock"


@pytest.mark.integration
def test_order_extract_upload_image_cloud_can_mock_vision_and_ai_separately(
    monkeypatch: pytest.MonkeyPatch,
):
    """Image uploads always run vision->marker-text.

    In mock mode (`use_mock=true`), the endpoint assumes all required fixtures exist.
    For image uploads this includes BOTH:
    - vision->marker-text fixture
    - cloud extract fixture
    """

    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    reload_config()
    import xscanner.server.persistence as persistence

    persistence._supabase_client = None  # type: ignore[attr-defined]

    img_path = Path(__file__).resolve().parents[2] / "invoices" / "72056547.jpg"
    assert img_path.exists(), f"Missing sample image at {img_path}"

    expected_ai_name = build_order_extract_mock_name_from_upload_filename(
        upload_filename="72056547.jpg"
    )
    expected_vision_name = build_order_vision_mock_name_from_upload_filename(
        upload_filename="72056547.jpg"
    )

    has_ai_fixture = get_order_extract_mock_path(expected_ai_name).exists()
    has_vision_fixture = get_order_vision_mock_path(expected_vision_name).exists()

    if not has_ai_fixture or not has_vision_fixture:
        pytest.skip(
            "Required recorded fixtures missing. Record them via: "
            "`make record-order-vision-mock FILE=invoices/72056547.jpg` and "
            "`make record-order-extract-mock FILE=invoices/72056547.pdf NAME="
            f"{expected_ai_name}`."
        )

    with TestClient(app) as client:
        with img_path.open("rb") as f:
            response = client.post(
                "/order/extract/upload",
                params={
                    "strategy": "cloud",
                    "use_mock": "true",
                    "debug": "true",
                },
                files={"files": ("72056547.jpg", f, "image/jpeg")},
            )

    assert response.status_code == 200
    payload = response.json()

    assert payload["success"] is True
    assert payload.get("error") is None

    result = payload["result"]
    raw = result.get("raw")
    assert isinstance(raw, dict)
    trace = raw.get("trace")
    assert isinstance(trace, dict)

    def iter_spans(node: object):
        if not isinstance(node, dict):
            return
        if node.get("type") == "span":
            yield node
        for child in node.get("children") or []:
            yield from iter_spans(child)

    # AI is mocked via existing mechanism.
    cloud_span = next(
        (sp for sp in iter_spans(trace) if sp.get("name") == "cloud.ai_extract"), None
    )
    assert isinstance(cloud_span, dict)
    cloud_attrs = cloud_span.get("attrs")
    assert isinstance(cloud_attrs, dict)
    assert cloud_attrs.get("provider") == "mock"
