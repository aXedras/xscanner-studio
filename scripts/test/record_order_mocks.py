"""Record per-step mock fixtures for /order/extract/upload.

Goal: allow integration tests (and local dev) to mock individual sub-steps
without mocking the entire endpoint response.

Records:
    1) Vision -> marker-text fixture (src/xscanner/mockdata/order_vision/)
        2) Cloud extract fixture (src/xscanner/mockdata/order_extract/)

Naming:
  Fixture names are derived from the upload filename (must match the filename
  the client sends). For multi-image uploads, the first image filename is used
  (matching server-side selection).

Usage (from repo root):
    venv/bin/python scripts/test/record_order_mocks.py --file invoices/72056547-image.pdf
    venv/bin/python scripts/test/record_order_mocks.py --files invoices/p1.jpg invoices/p2.jpg

Requires (recording mode):
    - OPENAI_API_KEY set
    - PyMuPDF installed when recording from PDF for vision
"""

from __future__ import annotations

import argparse
from pathlib import Path

from _order_mocks_recorder import is_pdf, record_from_images, record_from_pdf


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()

    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", required=False, help="Path to a PDF or single image")
    group.add_argument(
        "--files",
        nargs="+",
        required=False,
        help="Paths to one-or-more image files (multi-page upload)",
    )

    p.add_argument("--overwrite", action="store_true", help="Overwrite existing fixtures")
    return p.parse_args()


def main() -> None:
    args = _parse_args()

    overwrite = bool(args.overwrite)

    if args.file:
        input_path = Path(args.file)
        if not input_path.exists():
            raise SystemExit(f"File not found: {input_path}")

        if is_pdf(input_path):
            record_from_pdf(input_path=input_path, overwrite=overwrite)
        else:
            record_from_images(input_paths=[input_path], overwrite=overwrite)
        return

    input_paths = [Path(p) for p in (args.files or [])]
    for p in input_paths:
        if not p.exists():
            raise SystemExit(f"File not found: {p}")
        if is_pdf(p):
            raise SystemExit("--files only supports images (PDF not allowed)")

    record_from_images(input_paths=input_paths, overwrite=overwrite)


if __name__ == "__main__":
    main()
