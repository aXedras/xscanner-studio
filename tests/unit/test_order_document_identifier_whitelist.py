from xscanner.server.order.processing.document_detection import OrderDocumentDetection


def test_whitelist_provider_extracts_reference_as_document_number() -> None:
    text = """
Yours faithfully
Bank Julius Baer & Co. Ltd.
www.juliusbaer.com
Contract Note | Reference: ZPM.25312.00069.00 | AVBAW 005
""".strip()

    detected = OrderDocumentDetection().detect(text)

    assert detected.document_issuer == "bank-julius-baer"
    assert detected.document_number == "ZPM.25312.00069.00"
