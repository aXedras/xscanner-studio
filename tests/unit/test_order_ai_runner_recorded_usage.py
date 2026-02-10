from __future__ import annotations

import json

from xscanner.server.order.ai.runner import order_ai_mock_response_text, run_order_extraction_via_ai


def test_run_order_extraction_via_ai_uses_llm_usage_from_recorded_mock_envelope() -> None:
    envelope = {
        "meta": {
            "llm_usage": {
                "provider": "openai",
                "model": "gpt-5.2",
                "input_tokens": 10,
                "output_tokens": 5,
                "total_tokens": 15,
            }
        },
        "raw": {"raw_kv": [], "raw_tables": []},
        "structured_data": {
            "document": {
                "document_issuer": "a-mark",
                "document_type": "invoice",
                "document_number": "720565",
                "document_date": "2025-09-03",
            },
            "parties": {},
            "order_terms": {"amounts": {}},
            "order_items": [
                {
                    "item": "Test",
                    "description": "Test",
                    "quantity": "1",
                    "serial_number": "",
                }
            ],
        },
    }

    with order_ai_mock_response_text(json.dumps(envelope)):
        res = run_order_extraction_via_ai(marker_text="x", issuer="a-mark", doc_type="invoice")

    # Recorded-mock mode runs via a local mock client.
    assert res.provider == "mock"

    # But usage metadata should reflect the recorded provider/model + tokens.
    assert res.usage == {
        "provider": "openai",
        "model": "gpt-5.2",
        "input_tokens": 10,
        "output_tokens": 5,
        "total_tokens": 15,
    }
