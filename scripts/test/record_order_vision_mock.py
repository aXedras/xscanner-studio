"""Record a real vision->marker-text response as a deterministic mock fixture.

This script calls the real AI provider (OpenAI) and stores the produced marker-text
so we can run integration tests and dev flows without external calls.

Usage (from repo root):
    venv/bin/python scripts/test/record_order_vision_mock.py --file invoices/72056547-image.pdf
    venv/bin/python scripts/test/record_order_vision_mock.py --file invoices/72056547.jpg

Requires:
  - OPENAI_API_KEY set
  - PyMuPDF installed when recording from PDF

Output:
    - writes src/xscanner/mockdata/order_vision/<name>.json
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image

from xscanner.mockdata.order_vision import (
    build_order_vision_mock_name_from_upload_filename,
    write_order_vision_mock,
)
from xscanner.server.order.ai.vision_prompt import run_order_vision_to_marker_text
from xscanner.server.order.processing.pdf_images import render_pdf_pages_to_png_bytes


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", required=False, help="Path to sample PDF or image file")
    group.add_argument(
        "--files",
        nargs="+",
        required=False,
        help="Paths to one-or-more image files (multi-page upload)",
    )
    p.add_argument(
        "--name",
        required=False,
        default=None,
        help=(
            "Fixture name (writes src/xscanner/mockdata/order_vision/<name>.json). "
            "If omitted, the name is derived deterministically from the upload filename."
        ),
    )
    p.add_argument("--overwrite", action="store_true", help="Overwrite existing fixture")
    return p.parse_args()


def _is_pdf(path: Path) -> bool:
    if path.suffix.lower() == ".pdf":
        return True
    return False


def _normalize_image_to_png_bytes(img_bytes: bytes) -> bytes:
    # Keep it consistent with server upload normalization.
    from io import BytesIO

    with Image.open(BytesIO(img_bytes)) as im:
        converted = im.convert("RGB")
        buf = BytesIO()
        converted.save(buf, format="PNG")
        return buf.getvalue()


def main() -> None:
    args = _parse_args()

    input_paths: list[Path]
    if args.file:
        input_paths = [Path(args.file)]
    else:
        input_paths = [Path(p) for p in (args.files or [])]

    if not input_paths:
        raise SystemExit("No input files")

    for p in input_paths:
        if not p.exists():
            raise SystemExit(f"File not found: {p}")

    upload_filename = input_paths[0].name
    name = args.name or build_order_vision_mock_name_from_upload_filename(
        upload_filename=upload_filename
    )

    is_pdf_input = len(input_paths) == 1 and _is_pdf(input_paths[0])

    if is_pdf_input:
        pdf_bytes = input_paths[0].read_bytes()
        pages = render_pdf_pages_to_png_bytes(pdf_bytes)
        if not pages:
            raise SystemExit("PDF rendered to zero pages")
        page_images = pages
        meta = {
            "source": "pdf",
            "pages": len(page_images),
            "upload_filename": upload_filename,
        }
    else:
        raws = [p.read_bytes() for p in input_paths]
        page_images = [_normalize_image_to_png_bytes(b) for b in raws]
        meta = {
            "source": "images" if len(page_images) > 1 else "image",
            "pages": len(page_images),
            "upload_filename": upload_filename,
            "files": [p.name for p in input_paths],
        }

    result = run_order_vision_to_marker_text(page_images=page_images)

    out_path = write_order_vision_mock(
        name=name,
        marker_text=result.marker_text,
        provider=result.provider,
        model=result.model,
        usage=result.usage,
        overwrite=bool(args.overwrite),
        meta=meta,
    )

    print(f"Recorded vision marker-text mock saved: {out_path}")
    print(f"Fixture name: {name}")


if __name__ == "__main__":
    main()
