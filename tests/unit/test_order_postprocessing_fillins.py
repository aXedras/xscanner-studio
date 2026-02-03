from datetime import date

from xscanner.server.order.processing.default_processor import parse_default_order


def test_default_processor_fills_value_date_from_order_date_when_missing() -> None:
    text = "Invoice Date: 2025-09-03 Invoice No: ABC-123 Total: $10.00"
    parsed = parse_default_order(text, issuer="unknown", doc_type="invoice")

    assert parsed.value_date == date(2025, 9, 3)
    assert parsed.extracted_data["order_terms"]["value_date"] == "2025-09-03"


def test_default_processor_keeps_shipping_date_none_when_missing() -> None:
    text = "Invoice Date: 2025-09-03 Invoice No: ABC-123 Total: $10.00"
    parsed = parse_default_order(text, issuer="unknown", doc_type="invoice")

    assert parsed.shipping_date is None
    assert parsed.extracted_data["order_terms"]["shipping_date"] is None


def test_default_processor_does_not_mask_value_date_when_label_present() -> None:
    text = "Invoice Date: 2025-09-03 Invoice No: ABC-123 VALUE DATE Total: $10.00"
    parsed = parse_default_order(text, issuer="unknown", doc_type="invoice")

    assert parsed.value_date is None
    assert parsed.extracted_data["order_terms"]["value_date"] is None


def test_default_processor_does_not_mask_shipping_date_when_label_present() -> None:
    text = "Invoice Date: 2025-09-03 Invoice No: ABC-123 EST. SHIP DATE Total: $10.00"
    parsed = parse_default_order(text, issuer="unknown", doc_type="invoice")

    assert parsed.shipping_date is None
    assert parsed.extracted_data["order_terms"]["shipping_date"] is None
