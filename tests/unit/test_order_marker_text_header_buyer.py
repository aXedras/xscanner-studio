from __future__ import annotations

from datetime import date

from xscanner.server.order.processing.marker_text import build_marker_text
from xscanner.server.order.processing.raw_signals_types import RawKeyValue, RawOrderData
from xscanner.server.order.types import ParsedOrder


def test_build_marker_text_injects_buyer_into_header_from_raw_kv() -> None:
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

    parsed = ParsedOrder(
        document_issuer="test",
        document_type="invoice",
        document_number="REF-1",
        document_date=date(2026, 1, 31),
        order_number="REF-1",
        order_date=date(2026, 1, 31),
        value_date=None,
        shipping_date=None,
        transaction_type=None,
        seller_name=None,
        buyer_name=None,
        currency=None,
        subtotal_amount=None,
        shipping_charges_amount=None,
        other_charges_amount=None,
        total_amount=None,
        raw_text="",
        extracted_data={},
        items=[],
    )

    marker_text = build_marker_text(
        normalized_text="INVOICE\nSome header\n",
        issuer="test",
        doc_type="invoice",
        document_number="REF-1",
        document_date=date(2026, 1, 31),
        parsed=parsed,
        raw=raw,
    )

    assert "__PARTIES__" not in marker_text

    lines = [ln for ln in marker_text.splitlines() if ln.strip()]
    header_idx = lines.index("__HEADER__")
    assert any(ln == "Buyer: BFI BULLION AG" for ln in lines[header_idx + 1 :])


def test_build_marker_text_injects_buyer_from_receiver_derived_kv() -> None:
    raw = RawOrderData(
        raw_text="",
        lines=(),
        key_values=(
            RawKeyValue(
                key="receiver",
                value="BFI BULLION AG",
                key_normalized="receiver",
                source="derived",
            ),
        ),
        tables=(),
        normalized_text=None,
    )

    marker_text = build_marker_text(
        normalized_text="INVOICE\nBFI BULLION AG\n",
        issuer="a-mark",
        doc_type="order_confirmation",
        document_number="720565",
        document_date=date(2025, 9, 3),
        parsed=None,
        raw=raw,
    )

    lines = [ln for ln in marker_text.splitlines() if ln.strip()]
    header_idx = lines.index("__HEADER__")
    header_body = lines[header_idx + 1 :]
    assert "Buyer: BFI BULLION AG" in header_body


def test_build_marker_text_falls_back_to_buyer_from_address_block_in_header() -> None:
    raw = RawOrderData(
        raw_text="",
        lines=(),
        key_values=(
            # Seller is determined from explicit header phrase.
            RawKeyValue(
                key="website_0",
                value="www.amark.com",
                key_normalized="website",
                source="contact_regex",
            ),
            RawKeyValue(
                key="Address Block 0",
                value="BFI BULLION AG\nCHAMERSTASSE 174\nZUG, 6300\nSWITZERLAND",
                key_normalized="address_block_0",
                source="address_block_unlabeled",
            ),
        ),
        tables=(),
        normalized_text=None,
    )

    marker_text = build_marker_text(
        normalized_text="INVOICE / ORDER CONFIRMATION\nA-Mark is Selling\nBFI BULLION AG\n",
        issuer="a-mark",
        doc_type="order_confirmation",
        document_number="720565",
        document_date=date(2025, 9, 3),
        parsed=None,
        raw=raw,
    )

    lines = [ln for ln in marker_text.splitlines() if ln.strip()]
    header_idx = lines.index("__HEADER__")
    header_body = lines[header_idx + 1 :]
    assert "Seller: A-Mark" in header_body
    assert "Buyer: BFI BULLION AG" in header_body
