from __future__ import annotations

from datetime import date

from xscanner.server.order.processing.marker_text import build_marker_text
from xscanner.server.order.processing.raw_signals_types import RawKeyValue, RawOrderData, RawTable
from xscanner.server.order.types import ParsedOrder


def test_build_marker_text_matches_vision_contract_shape() -> None:
    raw = RawOrderData(
        raw_text="",
        lines=(),
        key_values=(),
        tables=(
            RawTable(
                name="order_items",
                headers=("item", "quantity", "description", "unit_price", "total_price"),
                rows=(("A1234", "2", "1 oz Gold Bar", "$100.00", "$200.00"),),
                source="unit-test",
            ),
        ),
        normalized_text=None,
    )

    parsed = ParsedOrder(
        document_issuer="test",
        document_type="invoice",
        document_number="72056547",
        document_date=date(2026, 1, 31),
        order_number="72056547",
        order_date=date(2026, 1, 31),
        value_date=date(2026, 2, 1),
        shipping_date=date(2026, 2, 2),
        transaction_type="PHYSICAL",
        seller_name=None,
        buyer_name=None,
        currency="USD",
        subtotal_amount=100.0,
        shipping_charges_amount=5.0,
        other_charges_amount=None,
        total_amount=105.0,
        raw_text="",
        extracted_data={},
        items=[],
    )

    marker_text = build_marker_text(
        normalized_text="INVOICE\nSeller Inc\nITEM QUANTITY DESCRIPTION UNIT PRICE TOTAL PRICE\n",
        issuer="test",
        doc_type="invoice",
        document_number="72056547",
        document_date=date(2026, 1, 31),
        parsed=parsed,
        raw=raw,
    )

    lines = [ln for ln in marker_text.splitlines() if ln.strip()]

    # Contract: marker text should be marker-first, starting with __DOC_ID__.
    assert lines[0].startswith("__DOC_ID__")
    assert "issuer=test" in lines[0]
    assert "doc_type=invoice" in lines[0]
    assert "document_number=72056547" in lines[0]
    assert "document_date=2026-01-31" in lines[0]

    # Contract: __HEADER__ remains the first content section.
    assert "__HEADER__" in lines
    assert lines[1] == "__HEADER__"

    # Contract: terms section (if present) uses pipe-separated headers + pipe-separated values (no k=v).
    terms_headers = [ln for ln in lines if ln.startswith("__TERMS_HEADERS__")]
    terms_rows = [ln for ln in lines if ln.startswith("__TERMS_ROW__")]
    if terms_headers or terms_rows:
        assert terms_headers
        assert terms_rows
        assert "|" in terms_headers[0]
        assert "|" in terms_rows[0]
        assert "=" not in terms_rows[0]

    # Contract: item markers are key/value pairs, but should not leak internal provenance tags.
    order_item = next(ln for ln in lines if ln.startswith("__ORDER_ITEM__"))
    assert "source=" not in order_item
    assert "=" in order_item

    # Contract: totals section (if present) is multi-line.
    if "__TOTALS__" in lines:
        totals_idx = lines.index("__TOTALS__")
        assert any(
            lines[i]
            .lower()
            .startswith(("sub total:", "shipping charges:", "other charges:", "total:"))
            for i in range(totals_idx + 1, len(lines))
        )


def test_build_marker_text_includes_ai_friendly_items_from_generic_table() -> None:
    raw = RawOrderData(
        raw_text="",
        lines=(),
        key_values=(),
        tables=(
            RawTable(
                name="table_0",
                headers=("Quantity", "Description", "Currency", "Rate"),
                rows=(
                    (
                        "12'774.5",
                        "FINE GOLD 999.9\nSEC-NO 033178",
                        "CHF",
                        "88.64",
                    ),
                ),
                source="unit-test",
            ),
        ),
        normalized_text=None,
    )

    parsed = ParsedOrder(
        document_issuer="test",
        document_type="contract_note",
        document_number="REF-1",
        document_date=date(2026, 1, 31),
        order_number="REF-1",
        order_date=date(2026, 1, 31),
        value_date=date(2026, 2, 1),
        shipping_date=None,
        transaction_type="PHYSICAL",
        seller_name=None,
        buyer_name=None,
        currency="CHF",
        subtotal_amount=None,
        shipping_charges_amount=None,
        other_charges_amount=None,
        total_amount=None,
        raw_text="",
        extracted_data={},
        items=[],
    )

    marker_text = build_marker_text(
        normalized_text="Contract Note",
        issuer="test",
        doc_type="contract_note",
        document_number="REF-1",
        document_date=date(2026, 1, 31),
        parsed=parsed,
        raw=raw,
    )

    assert "__ITEM_HEADERS__ QUANTITY | DESCRIPTION | CURRENCY | RATE" in marker_text

    order_item = next(ln for ln in marker_text.splitlines() if ln.startswith("__ORDER_ITEM__"))
    assert "QUANTITY=12'774.5" in order_item
    assert "CURRENCY=CHF" in order_item
    assert "RATE=88.64" in order_item
    assert "FINE GOLD 999.9 SEC-NO 033178" in order_item


def test_build_marker_text_includes_totals_from_raw_kv_fallback() -> None:
    raw = RawOrderData(
        raw_text="",
        lines=(),
        key_values=(
            RawKeyValue(
                key="Total",
                value="EUR 123'456.78",
                key_normalized="total",
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

    assert "__TOTALS__" in marker_text
    assert "Total: EUR 123'456.78" in marker_text


def test_build_marker_text_includes_terms_from_raw_kv_fallback() -> None:
    raw = RawOrderData(
        raw_text="",
        lines=(),
        key_values=(
            RawKeyValue(
                key="Date",
                value="24.09.2025",
                key_normalized="date",
                source="unit-test",
            ),
            RawKeyValue(
                key="Value date",
                value="26.09.2025",
                key_normalized="value_date",
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

    assert "__TERMS_HEADERS__ ORDER DATE | VALUE DATE" in marker_text
    assert "__TERMS_ROW__ 24.09.2025 | 26.09.2025" in marker_text
