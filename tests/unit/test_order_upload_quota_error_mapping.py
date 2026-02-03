import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from xscanner.lib.trace_tree import TraceTree
from xscanner.server.server import app


def _make_png_bytes() -> bytes:
    img = Image.new("RGB", (8, 8), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_order_upload_maps_openai_insufficient_quota_to_http_429(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _StubResult:
        def __init__(self) -> None:
            trace = TraceTree.start(name="order.process")
            trace.finish_error(error=RuntimeError("OpenAI error 429: insufficient_quota"))

            self.success = False
            self.parsed = None
            self.result = {}
            self.persisted_extracted_data = {}
            self.trace = trace
            self.processing_time = 0.01
            self.strategy_used = "order/auto"
            self.error = (
                "Order strategy failed: RuntimeError: OpenAI error 429: "
                '{"error":{"code":"insufficient_quota"}}'
            )

    class _StubService:
        def extract(self, **_kwargs):  # type: ignore[no-untyped-def]
            return _StubResult()

    # Patch the route module-level import so the endpoint uses our stub.
    import xscanner.server.order.routes as order_routes

    monkeypatch.setattr(order_routes, "get_order_extraction_service", lambda: _StubService())

    png = _make_png_bytes()

    with TestClient(app) as client:
        response = client.post(
            "/order/extract/upload",
            files=[("files", ("page1.png", png, "image/png"))],
            params={"strategy": "auto"},
        )

    assert response.status_code == 429
    payload = response.json()
    assert isinstance(payload, dict)
    detail = payload.get("detail")
    assert isinstance(detail, dict)
    assert detail.get("code") == "insufficient_quota"
    assert detail.get("provider") == "openai"


def test_order_upload_maps_openai_rate_limit_to_http_429(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _StubResult:
        def __init__(self) -> None:
            trace = TraceTree.start(name="order.process")
            trace.finish_error(error=RuntimeError("OpenAI error 429: rate_limit_exceeded"))

            self.success = False
            self.parsed = None
            self.result = {}
            self.persisted_extracted_data = {}
            self.trace = trace
            self.processing_time = 0.01
            self.strategy_used = "order/auto"
            self.error = (
                "Order strategy failed: RuntimeError: OpenAI error 429: "
                '{"error":{"code":"rate_limit_exceeded"}}'
            )

    class _StubService:
        def extract(self, **_kwargs):  # type: ignore[no-untyped-def]
            return _StubResult()

    import xscanner.server.order.routes as order_routes

    monkeypatch.setattr(order_routes, "get_order_extraction_service", lambda: _StubService())

    png = _make_png_bytes()

    with TestClient(app) as client:
        response = client.post(
            "/order/extract/upload",
            files=[("files", ("page1.png", png, "image/png"))],
            params={"strategy": "auto"},
        )

    assert response.status_code == 429
    payload = response.json()
    assert isinstance(payload, dict)
    detail = payload.get("detail")
    assert isinstance(detail, dict)
    assert detail.get("code") == "rate_limited"
    assert detail.get("provider") == "openai"
