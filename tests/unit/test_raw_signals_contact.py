from __future__ import annotations

from xscanner.server.order.processing.raw_signals_contact import extract_contact_key_values


def test_extract_contact_key_values_extracts_phone_numbers_labeled() -> None:
    lines = (
        "Bank Julius Baer & Co. Ltd.",
        "T +41 (0) 58 888 1111, F +41 (0) 58 888 1122",
        "www.juliusbaer.com",
        "info@juliusbaer.com",
    )

    kv = extract_contact_key_values(lines)
    phones = [k.value for k in kv if k.key_normalized == "phone"]

    assert any("+41" in p and "1111" in p for p in phones)
    assert any("+41" in p and "1122" in p for p in phones)
