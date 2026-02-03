"""Shared logic for recording per-step fixtures for /order/extract/upload."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from xscanner.mockdata.order_extract import (
    build_order_extract_mock_name_from_upload_filename,
    write_order_extract_mock_text,
)
from xscanner.mockdata.order_vision import (
    build_order_vision_mock_name_from_upload_filename,
    write_order_vision_mock,
)
from xscanner.server.order.ai.runner import run_order_extraction_via_ai
from xscanner.server.order.ai.vision_prompt import run_order_vision_to_marker_text
from xscanner.server.order.processing.document_detection import OrderDocumentDetection
from xscanner.server.order.processing.marker_text import build_marker_text
from xscanner.server.order.processing.pdf_images import render_pdf_pages_to_png_bytes
from xscanner.server.order.processing.pdf_text import extract_text_from_pdf_bytes
from xscanner.server.order.processing.pipeline import run_preprocessing
from xscanner.server.order.processing.raw_signals import extract_raw_order_data


def is_pdf(path: Path) -> bool:
    return path.suffix.lower() == ".pdf"


def normalize_image_to_png_bytes(img_bytes: bytes) -> bytes:
    from io import BytesIO

    with Image.open(BytesIO(img_bytes)) as im:
        converted = im.convert("RGB")
        buf = BytesIO()
        converted.save(buf, format="PNG")
        return buf.getvalue()


def record_from_pdf(*, input_path: Path, overwrite: bool) -> None:
    upload_filename = input_path.name
    pdf_bytes = input_path.read_bytes()

    vision_name = build_order_vision_mock_name_from_upload_filename(upload_filename=upload_filename)
    pages = render_pdf_pages_to_png_bytes(pdf_bytes)
    if not pages:
        raise SystemExit("PDF rendered to zero pages")

    vision = run_order_vision_to_marker_text(page_images=pages)
    vpath = write_order_vision_mock(
        name=vision_name,
        marker_text=vision.marker_text,
        provider=vision.provider,
        model=vision.model,
        usage=vision.usage,
        overwrite=overwrite,
        meta={"source": "pdf", "pages": len(pages), "upload_filename": upload_filename},
    )
    print(f"Recorded vision marker-text mock: {vpath}")

    extract_name = build_order_extract_mock_name_from_upload_filename(
        upload_filename=upload_filename
    )

    raw_text = extract_text_from_pdf_bytes(pdf_bytes)
    detector = OrderDocumentDetection()

    initial = detector.detect(raw_text)
    issuer = initial.document_issuer

    if issuer == "unknown":
        detected = detector.detect(vision.marker_text)
        issuer = detected.document_issuer or "unknown"
        doc_type = detected.document_type or "unknown"

        ai_result = run_order_extraction_via_ai(
            marker_text=vision.marker_text,
            issuer=issuer,
            doc_type=doc_type,
        )
    else:
        raw = extract_raw_order_data(raw_text)
        pre = run_preprocessing(raw, issuer, trace=[])
        normalized_text = pre.normalized_text or pre.raw_text
        identity = detector.detect(normalized_text, issuer_hint=issuer)

        marker_text = build_marker_text(
            normalized_text=normalized_text,
            issuer=issuer,
            doc_type=identity.document_type,
            document_number=identity.document_number,
            document_date=identity.document_date,
            parsed=None,
            raw=pre,
        )

        ai_result = run_order_extraction_via_ai(
            marker_text=marker_text,
            issuer=issuer,
            doc_type=identity.document_type,
        )

    import json

    envelope = json.loads(ai_result.raw_text)
    if not isinstance(envelope, dict):
        raise SystemExit("AI response is not a JSON object")

    meta = envelope.get("meta")
    if not isinstance(meta, dict):
        raise SystemExit("AI response meta must be a JSON object")

    usage = ai_result.usage if isinstance(ai_result.usage, dict) else {}
    meta["llm_usage"] = {
        "provider": ai_result.provider,
        "model": ai_result.model,
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "total_tokens": usage.get("total_tokens"),
    }

    apath = write_order_extract_mock_text(
        name=extract_name,
        text=json.dumps(envelope, ensure_ascii=False, indent=2),
        overwrite=overwrite,
    )
    print(f"Recorded extract mock: {apath}")


def record_from_images(*, input_paths: list[Path], overwrite: bool) -> None:
    if not input_paths:
        raise SystemExit("No input images")

    upload_filename = input_paths[0].name

    raws = [p.read_bytes() for p in input_paths]
    page_images = [normalize_image_to_png_bytes(b) for b in raws]

    vision_name = build_order_vision_mock_name_from_upload_filename(upload_filename=upload_filename)
    vision = run_order_vision_to_marker_text(page_images=page_images)
    vpath = write_order_vision_mock(
        name=vision_name,
        marker_text=vision.marker_text,
        provider=vision.provider,
        model=vision.model,
        usage=vision.usage,
        overwrite=overwrite,
        meta={
            "source": "images" if len(page_images) > 1 else "image",
            "pages": len(page_images),
            "upload_filename": upload_filename,
            "files": [p.name for p in input_paths],
        },
    )
    print(f"Recorded vision marker-text mock: {vpath}")

    extract_name = build_order_extract_mock_name_from_upload_filename(
        upload_filename=upload_filename
    )

    detector = OrderDocumentDetection()
    detected = detector.detect(vision.marker_text)
    issuer = detected.document_issuer or "unknown"
    doc_type = detected.document_type or "unknown"

    ai_result = run_order_extraction_via_ai(
        marker_text=vision.marker_text,
        issuer=issuer,
        doc_type=doc_type,
    )

    envelope = json.loads(ai_result.raw_text)
    if not isinstance(envelope, dict):
        raise SystemExit("AI response is not a JSON object")

    meta = envelope.get("meta")
    if not isinstance(meta, dict):
        raise SystemExit("AI response meta must be a JSON object")

    usage = ai_result.usage if isinstance(ai_result.usage, dict) else {}
    meta["llm_usage"] = {
        "provider": ai_result.provider,
        "model": ai_result.model,
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "total_tokens": usage.get("total_tokens"),
    }

    apath = write_order_extract_mock_text(
        name=extract_name,
        text=json.dumps(envelope, ensure_ascii=False, indent=2),
        overwrite=overwrite,
    )
    print(f"Recorded AI extract mock: {apath}")
