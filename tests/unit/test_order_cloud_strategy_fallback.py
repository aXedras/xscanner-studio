import xscanner.server.order.strategy.cloud as cloud_mod
from xscanner.server.order.strategy.cloud import CloudOrderParsingStrategy


def test_cloud_strategy_falls_back_to_default_parser_when_ai_fails(monkeypatch) -> None:
    def _boom(*_args, **_kwargs):
        raise RuntimeError("OpenAI error 401: invalid_api_key")

    monkeypatch.setattr(cloud_mod, "run_order_extraction_via_ai", _boom)

    marker_text = """
__DOC_ID__ issuer=a-mark | doc_type=order_confirmation | document_number=1234567 | document_date=2025-01-26
__ITEM_HEADERS__ QTY | DESCRIPTION
__ORDER_ITEM__ quantity=1 | description=1 kg Valcambi cast silver bar
""".strip()

    res = CloudOrderParsingStrategy().extract_from_text(marker_text, issuer_hint="a-mark")

    assert res.parsed is not None
    assert res.error is not None
    assert "AI extraction failed" in res.error

    assert res.parsed.items
    assert res.parsed.items[0]["quantity"] == "1"
    assert "Valcambi" in (res.parsed.items[0]["description"] or "")
