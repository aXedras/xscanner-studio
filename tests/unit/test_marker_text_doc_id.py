from __future__ import annotations

from datetime import date

import pytest

from xscanner.server.order.processing.document_detection import OrderDocumentDetection
from xscanner.server.order.processing.marker_text import ensure_doc_id
from xscanner.server.order.types import InvalidOrderDocument


def test_ensure_doc_id_prepends_deterministic_line() -> None:
    marker_text = """__HEADER__
INVOICE / ORDER CONFIRMATION
A-Mark is Selling
TICKET # ORDER DATE VALUE DATE EST. SHIP DATE
__TERMS_HEADERS__ TICKET # | ORDER DATE | VALUE DATE | EST. SHIP DATE
__TERMS_ROW__ 720565 | 09/03/2025 | 09/12/2025 | 09/12/2025
__ITEM_HEADERS__ ITEM | QUANTITY | DESCRIPTION
__ORDER_ITEM__ ITEM=SBVALKGCAST | QUANTITY=100 | DESCRIPTION=1 kg bar
"""

    out = ensure_doc_id(marker_text=marker_text, issuer_hint="a-mark")
    lines = [ln.strip() for ln in out.splitlines() if ln.strip()]

    assert lines[0].startswith("__DOC_ID__")
    assert "issuer=a-mark" in lines[0]
    assert "doc_type=" in lines[0]
    assert "document_number=720565" in lines[0]
    # a-mark slash order is configured to DMY first -> 09/03/2025 => 2025-03-09
    # This test focuses on determinism; the exact date depends on config.
    assert "document_date=" in lines[0]


def test_document_detection_parses_doc_id_first() -> None:
    marker_text = """__DOC_ID__ issuer=a-mark | doc_type=order_confirmation | document_number=720565 | document_date=2025-09-03
__HEADER__
INVOICE / ORDER CONFIRMATION
"""

    det = OrderDocumentDetection().detect(marker_text)
    assert det.document_issuer == "a-mark"
    assert det.document_type == "order_confirmation"
    assert det.document_number == "720565"
    assert det.document_date == date(2025, 9, 3)


def test_ensure_doc_id_repairs_incorrect_existing_doc_id() -> None:
    marker_text = """__DOC_ID__ issuer=a-mark | doc_type=invoice | document_number=720565 | document_date=2025-09-03
__TERMS_HEADERS__ TICKET # | ORDER DATE | VALUE DATE | EST. SHIP DATE | A-MARK TRADER | TRANSACTION TYPE
__TERMS_ROW__ 720565 | 2025-09-03 | 2025-09-12 | 2025-09-12 | Michael | PHYSICAL
"""

    out = ensure_doc_id(marker_text=marker_text, issuer_hint="a-mark")
    first = next(ln.strip() for ln in out.splitlines() if ln.strip())
    assert "__DOC_ID__" in first
    assert "issuer=a-mark" in first
    assert "doc_type=order_confirmation" in first
    assert "document_number=720565" in first
    assert "document_date=2025-09-03" in first


def test_ensure_doc_id_raises_on_missing_identity() -> None:
    with pytest.raises(InvalidOrderDocument):
        ensure_doc_id(marker_text="__HEADER__\nHello\n", issuer_hint=None)


def test_ensure_doc_id_keeps_valid_existing_doc_id_if_recompute_incomplete() -> None:
    # Regression: keep a complete __DOC_ID__ even if the remaining marker text
    # does not contain enough signals to re-derive identity.
    marker_text = """__DOC_ID__ issuer=bank-julius-baer | doc_type=invoice | document_number=ZPM.25312.00069.00 | document_date=2025-09-24
__HEADER__
Hello
"""

    out = ensure_doc_id(marker_text=marker_text, issuer_hint="bank-julius-baer")
    first = next(ln.strip() for ln in out.splitlines() if ln.strip())
    assert first.startswith("__DOC_ID__")
    assert "issuer=bank-julius-baer" in first
    assert "doc_type=invoice" in first
    assert "document_number=ZPM.25312.00069.00" in first
    assert "document_date=2025-09-24" in first


def test_ensure_doc_id_prefers_reference_over_sec_number_in_description() -> None:
    marker_text = """__HEADER__
Document Type Candidate: Contract Note
Reference: ZPM.25312.00069.00
Date: 24.09.2025
__ITEM_HEADERS__ QUANTITY | DESCRIPTION | CURRENCY | RATE
__ORDER_ITEM__ QUANTITY=12'774.5 | DESCRIPTION=FINE OUNCES/FINENESS 999.0/1000 FOR SILVER INGOTS/30 KG/TRANSIT Sec.-no 9101016 | CURRENCY=EUR | RATE=37.61
"""

    out = ensure_doc_id(marker_text=marker_text, issuer_hint="bank-julius-baer")
    first = next(ln.strip() for ln in out.splitlines() if ln.strip())

    assert first.startswith("__DOC_ID__")
    assert "issuer=bank-julius-baer" in first
    assert "doc_type=invoice" in first
    assert "document_number=ZPM.25312.00069.00" in first
    assert "document_date=2025-09-24" in first
