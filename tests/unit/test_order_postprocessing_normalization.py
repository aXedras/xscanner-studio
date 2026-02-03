from datetime import date

from xscanner.server.order.processing.pipeline import run_postprocessing
from xscanner.server.order.types import ParsedOrder


def test_postprocessing_normalizes_empty_strings_and_formats_scalars() -> None:
    parsed = ParsedOrder(
        document_issuer="unknown",
        document_type="invoice",
        document_number="ABC-123",
        document_date=date(2026, 2, 1),
        order_number="",
        order_date=date(2026, 2, 1),
        value_date=None,
        shipping_date=None,
        transaction_type="",
        seller_name="",
        buyer_name="",
        currency="us$",
        subtotal_amount=None,
        shipping_charges_amount=0.0,
        other_charges_amount=None,
        total_amount=10.0,
        raw_text="dummy",
        extracted_data={
            "document": {
                "document_issuer": "unknown",
                "document_type": "invoice",
                "document_number": "ABC-123",
                "document_date": "01/02/2026",
            },
            "parties": {
                "seller_name": "",
                "buyer_name": " ",
                "shipping_from": None,
                "shipping_to": "",
            },
            "order_terms": {
                "currency": "us$",
                "order_date": "01/02/2026",
                "order_number": "",
                "shipping_date": "",
                "value_date": "",
                "transaction_type": "",
                "amounts": {
                    "subtotal": "",
                    "shipping_charges": "",
                    "other_charges": "",
                    "total": "$10",
                },
            },
            "order_items": [
                {
                    "item": "",
                    "description": "Test",
                    "quantity": "",
                    "serial_number": "",
                    "metal": "",
                    "weight": "",
                    "weight_unit": "",
                    "fineness": "",
                    "producer": "",
                    "form": "",
                }
            ],
        },
        items=[],
    )

    processed = run_postprocessing(parsed, issuer="unknown")

    parties = processed.extracted_data["parties"]
    assert parties["seller_name"] is None
    assert parties["buyer_name"] is None
    assert parties["shipping_to"] is None

    terms = processed.extracted_data["order_terms"]
    assert terms["currency"] == "USD"
    assert terms["transaction_type"] is None

    # Dates normalized from ParsedOrder to ISO.
    assert processed.extracted_data["document"]["document_date"] == "2026-02-01"
    assert terms["order_date"] == "2026-02-01"
    assert terms["shipping_date"] is None
    assert terms["value_date"] is None

    amounts = terms["amounts"]
    assert amounts["total"] == "10.00"
    assert amounts["shipping_charges"] == "0.00"

    # Subtotal fill-in should work after normalization.
    assert amounts["subtotal"] == "10.00"

    item = processed.extracted_data["order_items"][0]
    assert item["serial_number"] is None
