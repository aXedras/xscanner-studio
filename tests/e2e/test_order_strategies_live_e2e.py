"""End-to-end tests for Order extraction strategies.

These tests exercise the FastAPI endpoint and (optionally) make real external
calls (e.g. OpenAI) when the corresponding API keys are configured.

Goal:
- Use the repository's default PDF as baseline.
- Assert that other strategies (e.g. cloud) produce the same `structured_data`
  as the manual strategy.

Notes:
- If OPENAI_API_KEY is not configured, cloud strategy checks are skipped.
- Persistence is disabled for this test to avoid writing to Supabase.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from xscanner.server.config import get_config, reload_config
from xscanner.server.server import app

pytestmark = pytest.mark.e2e


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_order_pdf() -> Path:
    pdf_path = _repo_root() / "invoices" / "72056547.pdf"
    if not pdf_path.exists():
        raise RuntimeError(f"Missing sample PDF at {pdf_path}")
    return pdf_path


def _post_order_upload(
    *,
    client: TestClient,
    file_path: Path,
    params: dict[str, str],
) -> dict[str, Any]:
    with file_path.open("rb") as f:
        resp = client.post(
            "/order/extract/upload",
            params=params,
            files={"file": (file_path.name, f, "application/pdf")},
        )

    assert resp.status_code == 200, resp.text
    payload = resp.json()
    assert isinstance(payload, dict)
    return payload


def _structured_data(payload: dict[str, Any]) -> dict[str, Any]:
    assert payload.get("success") is True, payload
    result = payload.get("result")
    assert isinstance(result, dict)
    structured = result.get("structured_data")
    assert isinstance(structured, dict)
    return structured


def _pretty(obj: object) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True)


def _to_float(val: object) -> float | None:
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        s = val.strip()
        if not s:
            return None
        try:
            return float(s)
        except ValueError:
            return None
    return None


def _normalize_whitespace(val: str) -> str:
    return " ".join((val or "").strip().split())


def _canonicalize_party_text(val: object) -> object:
    if not isinstance(val, str):
        return val
    s = _normalize_whitespace(val)
    s = s.replace(",", " ")
    s = _normalize_whitespace(s)
    return s.upper()


def _canonicalize_structured_data(structured: dict[str, Any]) -> dict[str, Any]:
    """Normalize known formatting differences across strategies.

    We keep this intentionally small and explicit: it's used for E2E
    equivalence checks, not for production normalization.
    """

    doc = structured.get("document") if isinstance(structured.get("document"), dict) else {}
    issuer = (doc.get("document_issuer") or "").strip().lower()

    out: dict[str, Any] = json.loads(json.dumps(structured))

    # Document: normalize issuer casing. Cloud can return a mixed-case label;
    # manual detection uses a canonical slug.
    out_doc = out.get("document")
    if isinstance(out_doc, dict) and issuer:
        out_doc["document_issuer"] = issuer

    # Parties: canonicalize casing/punctuation.
    parties = out.get("parties")
    if isinstance(parties, dict):
        for key in ("seller_name", "buyer_name", "shipping_from", "shipping_to"):
            if key in parties:
                parties[key] = _canonicalize_party_text(parties.get(key))

        # Issuer-specific seller canonicalization.
        if issuer == "a-mark":
            seller = parties.get("seller_name")
            if isinstance(seller, str) and "A-MARK" in seller:
                parties["seller_name"] = "A-MARK"

    # Order items: normalize empty strings and weight units.
    items = out.get("order_items")
    if isinstance(items, list):
        for item in items:
            if not isinstance(item, dict):
                continue

            for opt in ("serial_number", "fineness"):
                if opt in item and isinstance(item.get(opt), str) and not item[opt].strip():
                    item[opt] = None

            weight = _to_float(item.get("weight"))
            unit = (item.get("weight_unit") or "").strip().lower()
            if weight is not None and unit in {"g", "kg"}:
                weight_g = weight * 1000.0 if unit == "kg" else weight
                # Prefer an integer representation if possible.
                if abs(weight_g - round(weight_g)) < 1e-9:
                    item["weight"] = str(int(round(weight_g)))
                else:
                    item["weight"] = str(weight_g)
                item["weight_unit"] = "g"

    return out


def test_order_strategies_live_match_manual_baseline(
    monkeypatch: pytest.MonkeyPatch,
    quality_check_mode: bool,
):
    """Compare live strategy outputs against manual baseline.

    This asserts that `structured_data` is identical across strategies for the
    default sample PDF.

    In "quality check" mode we report mismatches but don't fail the test.
    """

    # Disable persistence for this test run.
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    reload_config()
    import xscanner.server.persistence as persistence

    persistence._supabase_client = None  # type: ignore[attr-defined]

    cfg = get_config()
    pdf_path = _default_order_pdf()

    with TestClient(app) as client:
        manual_payload = _post_order_upload(
            client=client,
            file_path=pdf_path,
            params={"strategy": "manual", "debug": "false"},
        )

        manual_structured = _structured_data(manual_payload)

        # Cloud strategy: real external call when configured.
        if not cfg.openai.api_key:
            pytest.skip("OPENAI_API_KEY not configured; skipping cloud live comparison")

        cloud_payload = _post_order_upload(
            client=client,
            file_path=pdf_path,
            params={"strategy": "cloud", "debug": "false"},
        )
        cloud_structured = _structured_data(cloud_payload)

    if cloud_structured != manual_structured:
        print("\nManual structured_data:")
        print(_pretty(manual_structured))
        print("\nCloud structured_data:")
        print(_pretty(cloud_structured))

        if quality_check_mode:
            # Quality-check mode: report but don't fail.
            return

    canonical_manual = _canonicalize_structured_data(manual_structured)
    canonical_cloud = _canonicalize_structured_data(cloud_structured)

    if canonical_cloud != canonical_manual:
        print("\nCanonical manual structured_data:")
        print(_pretty(canonical_manual))
        print("\nCanonical cloud structured_data:")
        print(_pretty(canonical_cloud))

        if quality_check_mode:
            return

        assert canonical_cloud == canonical_manual
