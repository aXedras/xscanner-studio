from __future__ import annotations

from datetime import date

from xscanner.server.order.processing.marker_text import build_marker_text
from xscanner.server.order.processing.raw_signals_types import RawKeyValue, RawOrderData


def test_build_marker_text_injects_seller_when_website_or_email_present() -> None:
    seller_block = "Bank Julius Baer & Co. Ltd.\nBahnhofstrasse 36\nCH-8010 Zurich"

    raw_website_only = RawOrderData(
        raw_text="",
        lines=(),
        key_values=(
            RawKeyValue(
                key="Address Block 0",
                value=seller_block,
                key_normalized="address_block_0",
                source="address_block_unlabeled",
            ),
            RawKeyValue(
                key="website_0",
                value="juliusbaer.com",
                key_normalized="website",
                source="contact_regex",
            ),
        ),
        tables=(),
        normalized_text=None,
    )

    mt_website = build_marker_text(
        normalized_text="CONTRACT NOTE\nSome header line\n",
        issuer="bank-julius-baer",
        doc_type="invoice",
        document_number="REF-1",
        document_date=date(2025, 9, 24),
        parsed=None,
        raw=raw_website_only,
    )
    assert "Seller: Bank Julius Baer & Co. Ltd." in mt_website

    raw_email_only = RawOrderData(
        raw_text="",
        lines=(),
        key_values=(
            RawKeyValue(
                key="Address Block 0",
                value=seller_block,
                key_normalized="address_block_0",
                source="address_block_unlabeled",
            ),
            RawKeyValue(
                key="email_0",
                value="info@juliusbaer.com",
                key_normalized="email",
                source="contact_regex",
            ),
        ),
        tables=(),
        normalized_text=None,
    )

    mt_email = build_marker_text(
        normalized_text="CONTRACT NOTE\nSome header line\n",
        issuer="bank-julius-baer",
        doc_type="invoice",
        document_number="REF-1",
        document_date=date(2025, 9, 24),
        parsed=None,
        raw=raw_email_only,
    )
    assert "Seller: Bank Julius Baer & Co. Ltd." in mt_email

    # If the contact domain doesn't match the seller name, do not inject.
    raw_mismatch = RawOrderData(
        raw_text="",
        lines=(),
        key_values=(
            RawKeyValue(
                key="Address Block 0",
                value=seller_block,
                key_normalized="address_block_0",
                source="address_block_unlabeled",
            ),
            RawKeyValue(
                key="website_0",
                value="example.com",
                key_normalized="website",
                source="contact_regex",
            ),
        ),
        tables=(),
        normalized_text=None,
    )

    mt_mismatch = build_marker_text(
        normalized_text="CONTRACT NOTE\nSome header line\n",
        issuer="bank-julius-baer",
        doc_type="invoice",
        document_number="REF-1",
        document_date=date(2025, 9, 24),
        parsed=None,
        raw=raw_mismatch,
    )
    assert "Seller: Bank Julius Baer & Co. Ltd." not in mt_mismatch

    raw_no_contact = RawOrderData(
        raw_text="",
        lines=(),
        key_values=(
            RawKeyValue(
                key="Address Block 0",
                value=seller_block,
                key_normalized="address_block_0",
                source="address_block_unlabeled",
            ),
        ),
        tables=(),
        normalized_text=None,
    )

    mt_none = build_marker_text(
        normalized_text="CONTRACT NOTE\nSome header line\n",
        issuer="bank-julius-baer",
        doc_type="invoice",
        document_number="REF-1",
        document_date=date(2025, 9, 24),
        parsed=None,
        raw=raw_no_contact,
    )
    assert "Seller: Bank Julius Baer & Co. Ltd." not in mt_none


def test_build_marker_text_prefers_is_selling_over_address_block_for_seller() -> None:
    # Mirrors the A-Mark layout: header explicitly states seller, while the first
    # unlabeled address block is the buyer.
    raw = RawOrderData(
        raw_text="",
        lines=(),
        key_values=(
            RawKeyValue(
                key="Address Block 0",
                value="BFI BULLION AG\nCHAMERSTASSE 174\nZUG, 6300\nSWITZERLAND",
                key_normalized="address_block_0",
                source="address_block_unlabeled",
            ),
            RawKeyValue(
                key="email_0",
                value="operations@amark.com",
                key_normalized="email",
                source="contact_regex",
            ),
            RawKeyValue(
                key="website_0",
                value="www.amark.com",
                key_normalized="website",
                source="contact_regex",
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
    assert "Seller: BFI BULLION AG" not in header_body


def test_build_marker_text_chooses_best_address_block_for_seller() -> None:
    # Fallback mode: no explicit "is Selling" line.
    # address_block_0 is buyer; address_block_1 is seller.
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
            RawKeyValue(
                key="Address Block 0",
                value="BFI BULLION AG\nCHAMERSTASSE 174\nZUG, 6300\nSWITZERLAND",
                key_normalized="address_block_0",
                source="address_block_unlabeled",
            ),
            RawKeyValue(
                key="Address Block 1",
                value="A-Mark Precious Metals, Inc.\n123 Main St\nLos Angeles, CA",
                key_normalized="address_block_1",
                source="address_block_unlabeled",
            ),
            RawKeyValue(
                key="website_0",
                value="www.amark.com",
                key_normalized="website",
                source="contact_regex",
            ),
        ),
        tables=(),
        normalized_text=None,
    )

    marker_text = build_marker_text(
        normalized_text="INVOICE / ORDER CONFIRMATION\nBFI BULLION AG\n",
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

    assert "Seller: A-Mark Precious Metals, Inc." in header_body
    assert "Seller: BFI BULLION AG" not in header_body
