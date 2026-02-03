from __future__ import annotations

from xscanner.server.order.processing.marker_text_raw_signals import (
    extract_raw_order_data_from_marker_text,
)
from xscanner.server.order.processing.marker_text_transform import (
    canonicalize_marker_text_for_ai,
)


def test_marker_text_multiline_terms_and_items_are_parsed() -> None:
    marker_text = """__HEADER__
INVOICE / ORDER CONFIRMATION

__TERMS_HEADERS__
TICKET # | ORDER DATE | VALUE DATE
__TERMS_ROW__
720565 | 09/03/2025 | 09/12/2025

__ITEM_HEADERS__
ITEM | QUANTITY | DESCRIPTION | UNIT PRICE | TOTAL PRICE
__ORDER_ITEM__
ticket #=SBVALKGCAST | qty=100 | description=1 kg Valcambi cast silver bar | unit price=$1,350.00 | total=$135,000.00
"""

    raw = extract_raw_order_data_from_marker_text(marker_text)

    terms = next(t for t in raw.tables if t.name == "terms")
    assert "order_date" not in terms.headers  # we do not canonicalize terms headers here
    assert terms.rows[0][0] == "720565"
    assert terms.rows[0][1] == "09/03/2025"

    items = next(t for t in raw.tables if t.name == "order_items")
    assert items.headers[:3] == ("item", "quantity", "description")
    assert items.rows[0][0] == "SBVALKGCAST"
    assert items.rows[0][1] == "100"
    assert "Valcambi" in items.rows[0][2]


def test_canonicalize_marker_text_for_ai_merges_multiline_markers() -> None:
    marker_text = """__HEADER__
INVOICE

__TERMS_HEADERS__
A | B
__TERMS_ROW__
1 | 2

__ITEM_HEADERS__
ITEM | QUANTITY
__ORDER_ITEM__
qty=2 | ticket #=ABC
"""

    out = canonicalize_marker_text_for_ai(marker_text)

    assert "__TERMS_HEADERS__ A | B" in out
    assert "__TERMS_ROW__ 1 | 2" in out
    assert (
        "__ITEM_HEADERS__ item | quantity | description | weight | weight_unit | item_price | total_price | serial_number"
        in out
    )
    # Key aliases should be canonicalized and on the same line.
    assert "__ORDER_ITEM__ item=ABC | quantity=2" in out
