import json

from xscanner.server.order.ai.extract_prompt import build_order_extract_messages


def _extract_adapter_hints_json(user_content: str) -> dict:
    marker = "ADAPTER_HINTS_JSON:\n"
    start = user_content.index(marker) + len(marker)
    end = user_content.index("\n\nDOCUMENT_TEXT", start)
    return json.loads(user_content[start:end])


def test_build_order_extract_messages_uses_config_prompt_and_hints():
    messages = build_order_extract_messages(
        marker_text="HELLO_MARKER_TEXT", issuer="Heraeus", doc_type="invoice"
    )

    assert len(messages) == 2
    assert messages[0].role == "system"
    assert messages[1].role == "user"

    # System prompt is loaded from config/order/prompts/order_extraction_cloud.md
    assert "ORDER_EXTRACTION_AI_CONTRACT" in messages[0].content
    assert "HARD RULES" in messages[0].content

    user = messages[1].content
    assert "ISSUER_HINT" in user
    assert "Heraeus" in user
    assert "DOCUMENT_TYPE_HINT" in user
    assert "invoice" in user
    assert "HELLO_MARKER_TEXT" in user

    hints = _extract_adapter_hints_json(user)

    # A few smoke checks that real whitelist content is present.
    assert "ALLOWED_PRODUCERS" in hints
    assert "Valcambi" in hints["ALLOWED_PRODUCERS"]
    assert "PRODUCER_ALIASES" in hints
    assert hints["PRODUCER_ALIASES"].get("Argor") == "Argor-Heraeus"
