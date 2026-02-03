from xscanner.server.order.processing.raw_signals import extract_raw_order_data


def _kv_map(raw_kv: tuple) -> dict[str, str]:
    return {kv.key_normalized: kv.value for kv in raw_kv}


def _values_for(raw_kv: tuple, key_normalized: str) -> list[str]:
    return [kv.value for kv in raw_kv if kv.key_normalized == key_normalized]


def test_extract_raw_order_data_splits_compound_inline_pairs() -> None:
    raw_text = "EMAIL: operations@amark.com PHONE: (310) 587-1477 WEBSITE: www.amark.com"

    raw = extract_raw_order_data(raw_text)
    kv = _kv_map(raw.key_values)

    assert kv["email"] == "operations@amark.com"
    assert kv["phone"] == "(310) 587-1477"
    assert kv["website"] == "www.amark.com"


def test_extract_raw_order_data_splits_compound_with_separators() -> None:
    raw_text = "Email: operations@amark.com; Phone: 123 | Website: example.com"

    raw = extract_raw_order_data(raw_text)
    kv = _kv_map(raw.key_values)

    assert kv["email"] == "operations@amark.com"
    assert kv["phone"] == "123"
    assert kv["website"] == "example.com"


def test_extract_raw_order_data_does_not_split_on_url_scheme() -> None:
    raw_text = "NOTE: HTTP://example.com PHONE: 123"

    raw = extract_raw_order_data(raw_text)
    kv = _kv_map(raw.key_values)

    assert kv["note"] == "HTTP://example.com"
    assert kv["phone"] == "123"


def test_extract_raw_order_data_extracts_unlabeled_email_and_website() -> None:
    raw_text = """
ACME Inc
For questions contact support@acme.example.
Visit https://www.acme.example/support
""".strip()

    raw = extract_raw_order_data(raw_text)

    emails = _values_for(raw.key_values, "email")
    websites = _values_for(raw.key_values, "website")

    assert "support@acme.example" in emails
    assert "acme.example" in websites


def test_extract_raw_order_data_dedupes_regex_website_when_labeled_exists() -> None:
    raw_text = """
WEBSITE: www.amark.com
More info at https://www.amark.com/contact
""".strip()

    raw = extract_raw_order_data(raw_text)
    websites = _values_for(raw.key_values, "website")

    # Keep the labeled value; do not add a second canonicalized website.
    assert websites == ["www.amark.com"]


def test_extract_raw_order_data_marker_text_extracts_unlabeled_contact_signals() -> None:
    marker_text = """
__HEADER__
INVOICE
support@acme.example
www.acme.example
""".strip()

    raw = extract_raw_order_data(marker_text)
    emails = _values_for(raw.key_values, "email")
    websites = _values_for(raw.key_values, "website")

    assert emails == ["support@acme.example"]
    assert websites == ["acme.example"]


def test_extract_raw_order_data_merges_multiline_description_row_in_table() -> None:
    raw_text = """
Quantity                   Description                                           Currency                                      Rate
12'774.5                   FINE OUNCES/FINENESS 999.0/1000                        EUR                                           37.61
                           FOR SILVER INGOTS/30 KG/TRANSIT
                           Sec.-no 9101016

                           Total                                                  EUR
""".strip("\n")

    raw = extract_raw_order_data(raw_text)
    assert raw.tables

    t = raw.tables[0]
    assert list(t.headers) == ["Quantity", "Description", "Currency", "Rate"]
    assert len(t.rows) == 1

    row = t.rows[0]
    assert row[0] == "12'774.5"
    assert "FINE OUNCES/FINENESS" in row[1]
    assert "FOR SILVER INGOTS/30 KG/TRANSIT" in row[1]
    assert "Sec.-no 9101016" in row[1]
    assert row[2] == "EUR"
    assert row[3] == "37.61"


def test_extract_raw_order_data_extracts_document_type_and_reference_from_footer() -> None:
    raw_text = """
Yours faithfully
Bank Julius Baer & Co. Ltd.
Bahnhofstrasse 36, P.O. Box, CH-8010 Zurich
www.juliusbaer.com
Page 1 of 1
Contract Note | Reference: ZPM.25312.00069.00 | AVBAW 005
""".strip()

    raw = extract_raw_order_data(raw_text)

    doc_type_candidates = _values_for(raw.key_values, "document_type_candidate")
    refs = _values_for(raw.key_values, "reference")

    assert "Contract Note" in doc_type_candidates
    assert "ZPM.25312.00069.00" in refs


def test_extract_raw_order_data_parses_marker_text_order_items_table() -> None:
    marker_text = """
__HEADER__
INVOICE
Seller Inc
__ITEM_HEADERS__ item | quantity | description | weight | weight_unit | item_price | total_price | serial_number
__ORDER_ITEM__ item=A1234 | quantity=2 | description=1 oz Gold Bar | weight=1 | weight_unit=oz | item_price=$100.00 | total_price=$200.00
__TOTALS__
Total: $200.00
""".strip()

    raw = extract_raw_order_data(marker_text)
    assert any(t.name == "order_items" for t in raw.tables)

    t = next(t for t in raw.tables if t.name == "order_items")
    assert list(t.headers) == [
        "item",
        "quantity",
        "description",
        "weight",
        "weight_unit",
        "item_price",
        "total_price",
        "serial_number",
    ]
    assert len(t.rows) == 1
    assert t.rows[0][0] == "A1234"


def test_extract_raw_order_data_canonicalizes_document_faithful_item_headers() -> None:
    marker_text = """
__HEADER__
INVOICE
Seller Inc
__ITEM_HEADERS__ TICKET # | QTY | DESCRIPTION | UNIT PRICE | TOTAL
__ORDER_ITEM__ ticket #=A1234 | qty=2 | description=1 oz Gold Bar | unit price=$100.00 | total=$200.00
""".strip()

    raw = extract_raw_order_data(marker_text)
    t = next(t for t in raw.tables if t.name == "order_items")

    assert list(t.headers) == [
        "item",
        "quantity",
        "description",
        "item_price",
        "total_price",
    ]
    assert len(t.rows) == 1

    row = t.rows[0]
    assert row[0] == "A1234"
    assert row[1] == "2"
    assert row[2] == "1 oz Gold Bar"
    assert row[3] == "$100.00"
    assert row[4] == "$200.00"


def test_extract_raw_order_data_extracts_billing_address_block() -> None:
    raw_text = """
RECHNUNGSADRESSE:
Max Mustermann
Musterstrasse 12
12345 Musterstadt
Deutschland
""".strip()

    raw = extract_raw_order_data(raw_text)
    kv = _kv_map(raw.key_values)

    assert "billing_address" in kv
    assert "Musterstrasse" in kv["billing_address"]
    assert "12345" in kv["billing_address"]


def test_extract_raw_order_data_extracts_shipping_address_block() -> None:
    raw_text = """
LIEFERADRESSE:
Firma Beispiel AG
Hauptstrasse 1
8000 Z\u00fcrich
Schweiz
""".strip()

    raw = extract_raw_order_data(raw_text)
    kv = _kv_map(raw.key_values)

    assert "shipping_address" in kv
    assert "Hauptstrasse" in kv["shipping_address"]
    assert "8000" in kv["shipping_address"]


def test_extract_raw_order_data_does_not_guess_address_without_label() -> None:
    raw_text = """
ACME GmbH
Musterstrasse 12
12345 Musterstadt
""".strip()

    raw = extract_raw_order_data(raw_text)
    kv = _kv_map(raw.key_values)

    assert "billing_address" not in kv
    assert "shipping_address" not in kv


def test_extract_raw_order_data_extracts_unlabeled_address_block_from_header() -> None:
    raw_text = """
ACME GmbH
Musterstrasse 12
12345 Musterstadt
Deutschland

INVOICE / ORDER CONFIRMATION
ITEM   QUANTITY   DESCRIPTION   UNIT PRICE   TOTAL PRICE
""".strip()

    raw = extract_raw_order_data(raw_text)
    kv = _kv_map(raw.key_values)

    assert "address_block_0" in kv
    assert "Musterstrasse" in kv["address_block_0"]
    assert "12345" in kv["address_block_0"]


def test_extract_raw_order_data_does_not_extract_unlabeled_block_without_address_signals() -> None:
    raw_text = """
ACME GmbH
Operations Department
Invoice Team

INVOICE
""".strip()

    raw = extract_raw_order_data(raw_text)
    kv = _kv_map(raw.key_values)

    assert "address_block_0" not in kv
    assert "address_block_1" not in kv


def test_extract_raw_order_data_extracts_org_and_address_from_mixed_boilerplate_line() -> None:
    raw_text = (
        "Please check the trade details carefully and notify the Bank within 48 hours via e-mail "
        "or telephone should you identify any errors or discrepancies. Advice without signature "
        "Yours faithfully Bank Julius Baer & Co. Ltd. Bahnhofstrasse 36, P.O. Box, CH-8010 Zurich"
    )

    raw = extract_raw_order_data(raw_text)
    kv = _kv_map(raw.key_values)

    assert "address_block_0" in kv
    assert "Bank Julius Baer" in kv["address_block_0"]
    assert "Bahnhofstrasse" in kv["address_block_0"]
    assert "CH-8010" in kv["address_block_0"]
    assert "Please check" not in kv["address_block_0"]


def test_extract_raw_order_data_extracts_recipient_block_with_name_and_address() -> None:
    raw_text = """
INVOICE / ORDER CONFIRMATION
A-Mark is Selling
BFI BULLION AG
CHAMERSTASSE 174
ZUG, 6300
SWITZERLAND
TICKET # ORDER DATE VALUE DATE
""".strip()

    raw = extract_raw_order_data(raw_text)
    kv = _kv_map(raw.key_values)

    assert "address_block_0" in kv
    assert "BFI BULLION AG" in kv["address_block_0"]
    assert "CHAMERSTASSE" in kv["address_block_0"]
    assert "6300" in kv["address_block_0"]
    assert "A-Mark is Selling" not in kv["address_block_0"]


def test_extract_raw_order_data_unlabeled_address_carves_out_of_boilerplate_line() -> None:
    raw_text = """
Please check the trade details carefully and notify the Bank within 48 hours via e-mail or telephone should you identify any errors or discrepancies to the order placed with the Bank. The Bank reserves the right to cancel or correct the order within this period in case of obvious errors or discrepancies. Advice without signature Yours faithfully Bank Julius Baer & Co. Ltd. Bahnhofstrasse 36, P.O. Box, CH-8010 Zurich
""".strip()

    raw = extract_raw_order_data(raw_text)
    kv = _kv_map(raw.key_values)

    assert "address_block_0" in kv
    value = kv["address_block_0"]
    assert "Bank Julius Baer" in value
    assert "Bahnhofstrasse" in value
    assert "CH-8010" in value
    assert "Please check the trade details carefully" not in value
