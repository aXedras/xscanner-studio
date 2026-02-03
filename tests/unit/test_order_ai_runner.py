import json
from dataclasses import dataclass
from typing import Any

import pytest

from xscanner.ai.core.types import AiRequest, AiResponse, AiResponseFormatError, AiUsage
from xscanner.server.order.ai.runner import run_order_extraction_via_ai


@dataclass
class _FakeClient:
    response_text: str
    last_request: AiRequest | None = None

    def complete(self, request: AiRequest) -> AiResponse:
        self.last_request = request
        return AiResponse(
            text=self.response_text,
            provider="fake",
            model=request.model,
            usage=AiUsage(input_tokens=1, output_tokens=1, total_tokens=2),
            raw={
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                "_xscanner": {
                    "request_url": "https://api.openai.com/v1/chat/completions",
                    "request_payload": {
                        "model": request.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "SYS",
                                "content_len": 3,
                                "content_truncated": False,
                            }
                        ],
                    },
                    "request_attempts": [
                        {
                            "model": request.model,
                            "messages": [
                                {
                                    "role": "system",
                                    "content": "SYS",
                                    "content_len": 3,
                                    "content_truncated": False,
                                }
                            ],
                        }
                    ],
                },
            },
        )


def _valid_envelope() -> dict[str, Any]:
    return {
        "meta": {"any": "thing"},
        "raw": {"any": "thing"},
        "structured_data": {
            "document": {
                "document_issuer": "Heraeus",
                "document_type": "invoice",
                "document_number": "INV-1",
                "document_date": "2026-01-30",
            },
            "parties": {
                "seller_name": None,
                "buyer_name": None,
                "shipping_from": None,
                "shipping_to": None,
            },
            "order_terms": {
                "currency": "CHF",
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
            "order_items": [
                {
                    "item": "1 oz Gold Bar",
                    "description": "1 oz Gold Bar",
                    "quantity": "1",
                    "metal": "gold",
                    "weight": "1",
                    "weight_unit": "oz",
                    "fineness": "",
                    "producer": "Heraeus",
                    "form": "bar",
                    "item_price": None,
                    "total_price": None,
                }
            ],
        },
    }


def test_run_order_extraction_via_ai_requires_envelope_keys_exactly():
    client = _FakeClient(response_text=json.dumps({"structured_data": {}}))

    with pytest.raises(AiResponseFormatError):
        run_order_extraction_via_ai(
            marker_text="X",
            issuer="Heraeus",
            doc_type="invoice",
            client=client,
            model="fake-model",
        )


def test_run_order_extraction_via_ai_validates_structured_data_only_and_returns_envelope():
    envelope = _valid_envelope()
    client = _FakeClient(response_text=json.dumps(envelope))

    result = run_order_extraction_via_ai(
        marker_text="MARKER",
        issuer="Heraeus",
        doc_type="invoice",
        client=client,
        model="fake-model",
        temperature=0.0,
        max_output_tokens=123,
    )

    assert result.provider == "fake"
    assert result.model == "fake-model"
    assert result.envelope == envelope
    assert result.structured_data.document.document_number == "INV-1"

    assert result.request_url == "https://api.openai.com/v1/chat/completions"
    assert isinstance(result.request_payload, dict)
    assert (result.request_payload or {}).get("model") == "fake-model"
    assert isinstance(result.request_attempts, list)

    # Sanity check: request got built with our config-based system prompt.
    assert client.last_request is not None
    assert client.last_request.force_json is True
    assert len(client.last_request.messages) == 2
    assert "ORDER_EXTRACTION_AI_CONTRACT" in client.last_request.messages[0].content
