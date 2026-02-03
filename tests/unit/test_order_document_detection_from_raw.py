from xscanner.server.order.processing.document_detection import OrderDocumentDetection
from xscanner.server.order.processing.raw_signals import extract_raw_order_data
from xscanner.server.order.processing.raw_signals_types import RawKeyValue, RawOrderData


def test_detect_from_raw_prefers_reference_kv_token_over_numeric_fallback() -> None:
    # This reference id is not matched by the labeled doc-number regex (it contains dots),
    # so text-only detection tends to fall back to partial numeric tokens.
    raw_text = """
Reference: ZPM.25312.00069.00
Some unrelated numbers 25312 00069 00
""".strip()

    raw = extract_raw_order_data(raw_text)
    detected = OrderDocumentDetection().detect_from_raw(raw)

    assert detected.document_issuer == "unknown"
    assert detected.document_number == "ZPM.25312.00069.00"
    assert "ZPM.25312.00069.00" in detected.document_number_candidates


def test_detect_from_raw_uses_doc_meta_candidates_from_footer_style_line() -> None:
    # Footer-style identity lines are extracted into synthetic KV candidates.
    raw_text = """
Page 1 of 1
Contract Note | Reference: ZPM.25312.00069.00 | AVBAW 005
""".strip()

    raw = extract_raw_order_data(raw_text)
    detected = OrderDocumentDetection().detect_from_raw(raw)

    assert detected.document_number == "ZPM.25312.00069.00"
    assert "ZPM.25312.00069.00" in detected.document_number_candidates
    assert detected.document_type == "invoice"
    assert "invoice" in detected.document_type_candidates


def test_detect_from_raw_falls_back_to_ticket_number_from_text_when_kv_missing() -> None:
    raw_text = """
ORDER CONFIRMATION
TICKET # 1234567
ORDER DATE 01/26/2025
""".strip()

    raw = extract_raw_order_data(raw_text)
    detected = OrderDocumentDetection().detect_from_raw(raw)

    assert detected.document_number == "1234567"
    assert "1234567" in detected.document_number_candidates


def test_detect_from_raw_maps_document_type_candidate_even_with_trailing_punctuation() -> None:
    raw = RawOrderData(
        raw_text="",
        lines=(),
        key_values=(
            RawKeyValue(
                key="Document Type",
                value="Auftragsbestätigung:",
                key_normalized="document_type_candidate",
                source="test",
            ),
        ),
        tables=(),
        normalized_text=None,
    )

    detected = OrderDocumentDetection().detect_from_raw(raw)
    assert detected.document_type == "order_confirmation"
    assert "order_confirmation" in detected.document_type_candidates
