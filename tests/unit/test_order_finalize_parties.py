from __future__ import annotations

from datetime import date

from xscanner.server.order.processing.finalize import finalize_order_extraction
from xscanner.server.order.processing.raw_signals_types import RawKeyValue, RawOrderData
from xscanner.server.order.types import ParsedOrder


def test_finalize_fills_buyer_name_from_raw_kv_when_missing() -> None:
    parsed = ParsedOrder(
        document_issuer="bank-julius-baer",
        document_type="invoice",
        document_number="ZPM.25312.00069.00",
        document_date=date(2025, 9, 24),
        order_number="ZPM.25312.00069.00",
        order_date=date(2025, 9, 24),
        value_date=None,
        shipping_date=None,
        transaction_type=None,
        seller_name=None,
        buyer_name=None,
        currency="EUR",
        subtotal_amount=None,
        shipping_charges_amount=None,
        other_charges_amount=None,
        total_amount=None,
        raw_text="",
        extracted_data={
            "document": {
                "document_issuer": "bank-julius-baer",
                "document_type": "invoice",
                "document_number": "ZPM.25312.00069.00",
                "document_date": "2025-09-24",
            },
            "parties": {
                "seller_name": None,
                "buyer_name": None,
                "shipping_from": None,
                "shipping_to": None,
            },
            "order_terms": {
                "order_number": "ZPM.25312.00069.00",
                "order_date": "2025-09-24",
                "value_date": None,
                "shipping_date": None,
                "transaction_type": None,
                "currency": "EUR",
                "amounts": {
                    "subtotal": None,
                    "shipping_charges": None,
                    "other_charges": None,
                    "total": None,
                },
            },
            "order_items": [],
        },
        items=[],
    )

    raw = RawOrderData(
        raw_text="",
        lines=(),
        key_values=(
            RawKeyValue(
                key="Client",
                value="BFI BULLION AG",
                key_normalized="client",
                source="unit-test",
            ),
        ),
        tables=(),
        normalized_text=None,
    )

    finalized, _raw_debug = finalize_order_extraction(
        parsed,
        issuer="bank-julius-baer",
        doc_type="invoice",
        doc_type_candidates=["invoice"],
        doc_number_candidates=["ZPM.25312.00069.00"],
        raw=raw,
    )

    assert finalized.buyer_name == "BFI BULLION AG"
    assert finalized.extracted_data["parties"]["buyer_name"] == "BFI BULLION AG"


def test_finalize_does_not_override_existing_buyer_name() -> None:
    parsed = ParsedOrder(
        document_issuer="bank-julius-baer",
        document_type="invoice",
        document_number="ZPM.25312.00069.00",
        document_date=date(2025, 9, 24),
        order_number="ZPM.25312.00069.00",
        order_date=date(2025, 9, 24),
        value_date=None,
        shipping_date=None,
        transaction_type=None,
        seller_name=None,
        buyer_name="EXISTING BUYER",
        currency="EUR",
        subtotal_amount=None,
        shipping_charges_amount=None,
        other_charges_amount=None,
        total_amount=None,
        raw_text="",
        extracted_data={
            "document": {
                "document_issuer": "bank-julius-baer",
                "document_type": "invoice",
                "document_number": "ZPM.25312.00069.00",
                "document_date": "2025-09-24",
            },
            "parties": {
                "seller_name": None,
                "buyer_name": "EXISTING BUYER",
                "shipping_from": None,
                "shipping_to": None,
            },
            "order_terms": {
                "order_number": "ZPM.25312.00069.00",
                "order_date": "2025-09-24",
                "value_date": None,
                "shipping_date": None,
                "transaction_type": None,
                "currency": "EUR",
                "amounts": {
                    "subtotal": None,
                    "shipping_charges": None,
                    "other_charges": None,
                    "total": None,
                },
            },
            "order_items": [],
        },
        items=[],
    )

    raw = RawOrderData(
        raw_text="",
        lines=(),
        key_values=(
            RawKeyValue(
                key="Client",
                value="BFI BULLION AG",
                key_normalized="client",
                source="unit-test",
            ),
        ),
        tables=(),
        normalized_text=None,
    )

    finalized, _raw_debug = finalize_order_extraction(
        parsed,
        issuer="bank-julius-baer",
        doc_type="invoice",
        doc_type_candidates=["invoice"],
        doc_number_candidates=["ZPM.25312.00069.00"],
        raw=raw,
    )

    assert finalized.buyer_name == "EXISTING BUYER"
    assert finalized.extracted_data["parties"]["buyer_name"] == "EXISTING BUYER"
