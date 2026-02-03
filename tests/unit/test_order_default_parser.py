import pytest

from xscanner.server.order.processing.default_processor import (
    _extract_currency,
    _extract_document_date,
    _parse_money,
    parse_default_order,
)
from xscanner.server.order.processing.document_detection import OrderDocumentDetection


def test_best_effort_document_number_prefers_labeled_value() -> None:
    text = "Invoice No: ABC-123 some other numbers 999999"
    assert OrderDocumentDetection._extract_document_number(text) == "ABC-123"


@pytest.mark.parametrize(
    "numeric,expected",
    [
        ("$1,234.56", 1234.56),
        ("1.234,56 EUR", 1234.56),
        ("1234,56", 1234.56),
        ("1234.56", 1234.56),
        ("1 234.56", 1234.56),
    ],
)
def test_parse_money_handles_common_separators(numeric: str, expected: float) -> None:
    assert _parse_money(numeric) == pytest.approx(expected)


def test_best_effort_currency_detection() -> None:
    assert _extract_currency("Total: € 10.00") == "EUR"
    assert _extract_currency("Amount: CHF 10.00") == "CHF"
    assert _extract_currency("Total: $10.00") == "USD"


def test_best_effort_labeled_date_prefers_date_label() -> None:
    text = "Some header 01/01/2020 Invoice Date: 2025-01-26 Footer"
    assert _extract_document_date(text, issuer_hint="unknown").isoformat() == "2025-01-26"


def test_parse_default_order_handles_single_digit_slash_dates() -> None:
    text = (
        "TICKET # ORDER DATE VALUE DATE EST. SHIP DATE\n"
        "720565 9/3/2025 9/12/2025 9/12/2025 PHYSICAL\n"
        "Total: $10.00"
    )
    parsed = parse_default_order(text, issuer="unknown", doc_type="invoice")
    assert parsed.document_date.isoformat() == "2025-09-03"


def test_parse_default_order_builds_canonical_shape() -> None:
    text = "Invoice Date: 2025-01-26 Invoice No: ABC-123 Total: $1,234.56"
    parsed = parse_default_order(text, issuer="unknown", doc_type="invoice")

    assert parsed.document_number == "ABC-123"
    assert parsed.document_date.isoformat() == "2025-01-26"

    structured = parsed.extracted_data
    assert structured["document"]["document_number"] == "ABC-123"
    assert structured["order_terms"]["amounts"]["total"] == "1234.56"
    assert "order_items" in structured
    assert "line_items" not in structured


def test_parse_default_order_parses_total_with_currency_code_and_apostrophe_separators() -> None:
    text = "Invoice Date: 2025-01-26 Invoice No: ABC-123 Total: EUR 123'456.78"
    parsed = parse_default_order(text, issuer="unknown", doc_type="invoice")
    structured = parsed.extracted_data

    assert parsed.total_amount == pytest.approx(123456.78)
    assert structured["order_terms"]["amounts"]["total"] == "123456.78"


def test_parse_default_order_infers_item_from_description_when_missing() -> None:
    text = (
        "Invoice Date: 2025-01-26 Invoice No: ABC-123 Total: $10.00\n"
        "__ORDER_ITEM__ | description=FINE OUNCES/FINENESS 999.0/1000 FOR SILVER INGOTS/30 KG/TRANSIT Sec.-no 9101016\n"
    )
    parsed = parse_default_order(text, issuer="unknown", doc_type="invoice")
    structured = parsed.extracted_data

    assert structured["order_items"]
    assert structured["order_items"][0]["item"] == "30 kg silver bar"


def test_parse_default_order_maps_value_and_shipping_dates_by_label() -> None:
    text = (
        "Invoice Date: 2025-01-26 "
        "Invoice No: ABC-123 "
        "Value Date: 2025-02-01 "
        "Shipping Date: 2025-02-02 "
        "Total: $10.00"
    )
    parsed = parse_default_order(text, issuer="unknown", doc_type="invoice")

    assert parsed.value_date is not None
    assert parsed.value_date.isoformat() == "2025-02-01"
    assert parsed.shipping_date is not None
    assert parsed.shipping_date.isoformat() == "2025-02-02"

    structured = parsed.extracted_data
    assert structured["order_terms"]["value_date"] == "2025-02-01"
    assert structured["order_terms"]["shipping_date"] == "2025-02-02"


def test_parse_default_order_maps_value_and_shipping_dates_from_header_table_row() -> None:
    text = (
        "TICKET # ORDER DATE VALUE DATE EST. SHIP DATE\n"
        "720565 09/03/2025 09/12/2025 09/12/2025 PHYSICAL\n"
        "Total: $10.00"
    )
    parsed = parse_default_order(text, issuer="unknown", doc_type="invoice")

    assert parsed.document_number == "720565"
    assert parsed.document_date.isoformat() == "2025-09-03"

    assert parsed.value_date is not None
    assert parsed.value_date.isoformat() == "2025-09-12"
    assert parsed.shipping_date is not None
    assert parsed.shipping_date.isoformat() == "2025-09-12"


def test_parse_default_order_extracts_buyer_name_block_from_ship_to() -> None:
    text = (
        "Invoice Date: 2025-01-26 "
        "Invoice No: ABC-123 "
        "Ship To: ACME INC 123 MAIN ST SOMEWHERE CA 90210 "
        "Total: $10.00"
    )
    parsed = parse_default_order(text, issuer="unknown", doc_type="invoice")

    assert parsed.buyer_name is not None
    assert "ACME" in parsed.buyer_name
    assert "123 MAIN" in parsed.buyer_name

    structured = parsed.extracted_data
    assert structured["parties"]["buyer_name"] is not None
    assert "ACME" in structured["parties"]["buyer_name"]


def test_parse_default_order_sets_shipping_to_and_defaults_buyer_name_to_shipping_to() -> None:
    text = (
        "Invoice Date: 2025-01-26 "
        "Invoice No: ABC-123 "
        "Ship To: ACME INC 123 MAIN ST SOMEWHERE CA 90210 "
        "Total: $10.00"
    )
    parsed = parse_default_order(text, issuer="unknown", doc_type="invoice")
    structured = parsed.extracted_data

    assert structured["parties"]["shipping_to"] is not None
    assert "ACME" in structured["parties"]["shipping_to"]
    assert structured["parties"]["buyer_name"] == structured["parties"]["shipping_to"]


def test_parse_default_order_prefers_bill_to_for_buyer_name_when_present() -> None:
    text = (
        "Invoice Date: 2025-01-26 "
        "Invoice No: ABC-123 "
        "Ship To: SHIPPING RECIPIENT 9 ROAD TOWN "
        "Bill To: BILLING NAME 1 STREET CITY "
        "Total: $10.00"
    )
    parsed = parse_default_order(text, issuer="unknown", doc_type="invoice")
    structured = parsed.extracted_data

    assert structured["parties"]["shipping_to"] is not None
    assert "SHIPPING RECIPIENT" in structured["parties"]["shipping_to"]
    assert structured["parties"]["buyer_name"] is not None
    assert "BILLING NAME" in structured["parties"]["buyer_name"]


def test_parse_default_order_extracts_shipping_from() -> None:
    text = (
        "Invoice Date: 2025-01-26 "
        "Invoice No: ABC-123 "
        "Ship From: WAREHOUSE A 77 ROAD CITY "
        "Ship To: ACME INC 123 MAIN ST SOMEWHERE CA 90210 "
        "Total: $10.00"
    )
    parsed = parse_default_order(text, issuer="unknown", doc_type="invoice")
    structured = parsed.extracted_data

    assert structured["parties"]["shipping_from"] is not None
    assert "WAREHOUSE A" in structured["parties"]["shipping_from"]


def test_parse_default_order_extracts_buyer_name_from_buyer_label() -> None:
    text = "Invoice Date: 2025-01-26 Invoice No: ABC-123 Buyer: BFI BULLION AG Total: $10.00"
    parsed = parse_default_order(text, issuer="unknown", doc_type="invoice")
    structured = parsed.extracted_data

    assert parsed.buyer_name == "BFI BULLION AG"
    assert structured["parties"]["buyer_name"] == "BFI BULLION AG"
