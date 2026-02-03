from xscanner.server.order.processing.default_processor import parse_default_order


def test_default_processor_infers_bullion_fields_from_description() -> None:
    text = """TICKET # 12345
ORDER DATE 01/26/2025
__ORDER_ITEM__ item=SBVALKGCAST | quantity=100 | description=1 kg Valcambi cast silver bar | item_price=$1.00 | total_price=$100.00
"""

    parsed = parse_default_order(text=text, issuer="unknown", doc_type="invoice")
    assert parsed.items
    item = parsed.items[0]

    assert item["metal"] == "silver"
    assert item["weight"] == "1"
    assert item["weight_unit"] == "kg"
    assert item["producer"] == "Valcambi"
    assert item["form"] == "bar"


def test_default_processor_maps_rate_to_item_price_for_bank_tables() -> None:
    text = """TICKET # ZPM.25312.00069.00
ORDER DATE 24.09.2025
__ORDER_ITEM__ quantity=12'774.5 | description=FINE OUNCES/FINENESS 999.0/1000 FOR SILVER INGOTS/30 KG/TRANSIT Sec.-no 9101016 | currency=EUR | rate=37.61
"""

    parsed = parse_default_order(text=text, issuer="bank-julius-baer", doc_type="invoice")
    assert parsed.items
    item = parsed.items[0]

    assert item["quantity"] == "12'774.5"
    assert item["item_price"] == 37.61
    assert item["total_price"] is None
    assert item["serial_number"] == "9101016"
