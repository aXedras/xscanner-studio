from __future__ import annotations

from datetime import date

from xscanner.server.order.processing.marker_text import build_marker_text
from xscanner.server.order.processing.raw_signals_types import RawKeyValue, RawOrderData


def test_build_marker_text_injects_doc_meta_reference_and_doc_type_candidate() -> None:
    raw = RawOrderData(
        raw_text="",
        lines=(),
        key_values=(
            RawKeyValue(
                key="Document Type Candidate",
                value="Contract Note",
                key_normalized="document_type_candidate",
                source="doc_meta_regex",
            ),
            RawKeyValue(
                key="Reference",
                value="ZPM.25312.00069.00",
                key_normalized="reference",
                source="doc_meta_regex",
            ),
        ),
        tables=(),
        normalized_text=None,
    )

    marker_text = build_marker_text(
        normalized_text="CONTRACT NOTE\nSome header line\n",
        issuer="bank-julius-baer",
        doc_type="order_confirmation",
        document_number="SHOULD-NOT-MATTER",
        document_date=date(2025, 9, 24),
        parsed=None,
        raw=raw,
    )

    lines = [ln for ln in marker_text.splitlines() if ln.strip()]
    header_idx = lines.index("__HEADER__")
    assert lines[header_idx + 1] == "Document Type Candidate: Contract Note"
    assert lines[header_idx + 2] == "Reference: ZPM.25312.00069.00"


def test_build_marker_text_emits_contact_section_from_raw_signals() -> None:
    raw = RawOrderData(
        raw_text="",
        lines=(),
        key_values=(
            RawKeyValue(
                key="email_0",
                value="info@juliusbaer.com",
                key_normalized="email",
                source="contact_regex",
            ),
            RawKeyValue(
                key="website_0",
                value="juliusbaer.com",
                key_normalized="website",
                source="contact_regex",
            ),
            RawKeyValue(
                key="phone_0",
                value="+41 (0) 58 888 1111",
                key_normalized="phone",
                source="contact_regex",
            ),
        ),
        tables=(),
        normalized_text=None,
    )

    marker_text = build_marker_text(
        normalized_text="INVOICE\nSome header\n",
        issuer="test",
        doc_type="invoice",
        document_number="REF-1",
        document_date=date(2026, 1, 31),
        parsed=None,
        raw=raw,
    )

    assert "__CONTACT__" in marker_text
    assert "EMAIL: info@juliusbaer.com" in marker_text
    assert "PHONE: +41 (0) 58 888 1111" in marker_text
    assert "WEBSITE: juliusbaer.com" in marker_text
