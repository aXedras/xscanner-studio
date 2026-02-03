import pytest

from xscanner.server.order.processing.bullion_description_parser import (
    infer_fineness,
    infer_form,
    infer_item_name,
    infer_metal,
    infer_producer,
    infer_serial_number,
    infer_weight,
)


@pytest.mark.parametrize(
    "description,expected",
    [
        ("1 kg Valcambi cast silver bar", "silver"),
        ("100 oz GOLD BAR", "gold"),
        ("Platinum coin", "platinum"),
        ("Palladium round", "palladium"),
        ("XAU bar", "gold"),
        ("silber barren", "silver"),
        ("Something else", "unknown"),
        (None, "unknown"),
    ],
)
def test_infer_metal(description: str | None, expected: str) -> None:
    assert infer_metal(description) == expected


@pytest.mark.parametrize(
    "description,expected",
    [
        ("1 kg Valcambi cast silver bar", ("1", "kg")),
        ("0.5 oz gold coin", ("0.5", "oz")),
        ("1 ozt gold coin", ("1", "oz")),
        ("2 lbs silver bar", ("2", "lb")),
        ("weightless thing", (None, None)),
        (None, (None, None)),
    ],
)
def test_infer_weight(description: str | None, expected: tuple[str | None, str | None]) -> None:
    assert infer_weight(description) == expected


@pytest.mark.parametrize(
    "description,expected",
    [
        ("1 kg Valcambi cast silver bar", "Valcambi"),
        ("PAMP minted gold bar", "PAMP"),
        ("Argor Heraeus bar", "Argor-Heraeus"),
        ("Heraeus bar", "Heraeus"),
        ("RCM coin", "Royal Canadian Mint"),
        ("Unknown producer", None),
        (None, None),
    ],
)
def test_infer_producer(description: str | None, expected: str | None) -> None:
    assert infer_producer(description) == expected


@pytest.mark.parametrize(
    "description,expected",
    [
        ("Valcambi cast silver bar", "bar"),
        ("PAMP minted gold bar", "bar"),
        ("silver bar", "bar"),
        ("gold coin", "coin"),
        ("silver round", "round"),
        ("SILVER INGOTS/30 KG", "bar"),
        ("silver grain", "unknown"),
        ("silver shot", "unknown"),
        ("unknown form", "unknown"),
        (None, "unknown"),
    ],
)
def test_infer_form(description: str | None, expected: str | None) -> None:
    assert infer_form(description) == expected


@pytest.mark.parametrize(
    "description,expected",
    [
        (
            "FINE OUNCES/FINENESS 999.0/1000 FOR SILVER INGOTS/30 KG/TRANSIT Sec.-no 9101016",
            "30 kg silver bar",
        ),
        ("1 kg Valcambi cast silver bar", "Valcambi 1 kg silver bar"),
        ("No weight but silver bar", None),
        ("30 kg something", None),
        (None, None),
    ],
)
def test_infer_item_name(description: str | None, expected: str | None) -> None:
    assert infer_item_name(description) == expected


@pytest.mark.parametrize(
    "description,expected",
    [
        ("999.9 fine gold bar", "999.9"),
        ("fineness 0.9999 gold", "0.9999"),
        (".999 silver", "0.999"),
        ("no fineness", None),
        (None, None),
    ],
)
def test_infer_fineness(description: str | None, expected: str | None) -> None:
    assert infer_fineness(description) == expected


@pytest.mark.parametrize(
    "description,expected",
    [
        ("FINE GOLD 999.9 SEC-NO 033178", "033178"),
        ("... /TRANSIT Sec.-no 9101016", "9101016"),
        ("Serial No: AB 123 45", "AB 123 45"),
        ("No serial here", None),
        (None, None),
    ],
)
def test_infer_serial_number(description: str | None, expected: str | None) -> None:
    assert infer_serial_number(description) == expected
