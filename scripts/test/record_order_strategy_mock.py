"""Record a full strategy-level mock fixture for /order/extract/upload.

This is intentionally simple: it runs the chosen strategy end-to-end via the
OrderExtractionService and writes the resulting JSON envelope to
`src/xscanner/mockdata/order_strategy/`.

Usage (from repo root):
  venv/bin/python scripts/test/record_order_strategy_mock.py --strategy manual --file invoices/72056547.pdf
  venv/bin/python scripts/test/record_order_strategy_mock.py --strategy cloud --file invoices/72056547-image.pdf
  venv/bin/python scripts/test/record_order_strategy_mock.py --strategy cloud --files invoices/p1.jpg invoices/p2.jpg

Notes:
  - `strategy=cloud` requires OPENAI_API_KEY.
  - `strategy=manual` does not require API keys but only supports PDF-text inputs.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from _order_mocks_recorder import is_pdf, normalize_image_to_png_bytes

from xscanner.mockdata.order_strategy import (
    build_order_strategy_mock_name_from_upload_filename,
    write_order_strategy_mock_text,
)
from xscanner.server.order.service import get_order_extraction_service
from xscanner.server.order.strategy import OrderStrategyChoice


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()

    p.add_argument(
        "--strategy",
        required=True,
        choices=[c.value for c in OrderStrategyChoice],
        help="Order extraction strategy",
    )

    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", required=False, help="Path to a PDF or single image")
    group.add_argument(
        "--files",
        nargs="+",
        required=False,
        help="Paths to one-or-more image files (multi-page upload)",
    )

    p.add_argument(
        "--debug", action="store_true", help="Record debug envelope (includes raw section)"
    )
    p.add_argument("--overwrite", action="store_true", help="Overwrite existing fixtures")
    return p.parse_args()


def main() -> None:
    args = _parse_args()

    strategy = OrderStrategyChoice(str(args.strategy))
    overwrite = bool(args.overwrite)
    debug = bool(args.debug)

    service = get_order_extraction_service()

    if args.file:
        input_path = Path(args.file)
        if not input_path.exists():
            raise SystemExit(f"File not found: {input_path}")

        upload_filename = input_path.name

        if is_pdf(input_path):
            pdf_bytes = input_path.read_bytes()
            res = service.extract(
                pdf_bytes=pdf_bytes, page_images=None, strategy=strategy, debug=debug
            )
        else:
            img_bytes = input_path.read_bytes()
            page_images = [normalize_image_to_png_bytes(img_bytes)]
            res = service.extract(
                pdf_bytes=None, page_images=page_images, strategy=strategy, debug=debug
            )

    else:
        input_paths = [Path(p) for p in (args.files or [])]
        for p in input_paths:
            if not p.exists():
                raise SystemExit(f"File not found: {p}")
            if is_pdf(p):
                raise SystemExit("--files only supports images (PDF not allowed)")

        upload_filename = input_paths[0].name
        raws = [p.read_bytes() for p in input_paths]
        page_images = [normalize_image_to_png_bytes(b) for b in raws]
        res = service.extract(
            pdf_bytes=None, page_images=page_images, strategy=strategy, debug=debug
        )

    if not res.success:
        raise SystemExit(f"Extraction failed (strategy={strategy.value}): {res.error}")

    if not hasattr(res, "result"):
        raise SystemExit("Unexpected service result: missing 'result'")

    if not isinstance(res.result, dict) and hasattr(res.result, "model_dump"):
        payload = res.result.model_dump()
    else:
        payload = res.result

    if not isinstance(payload, dict):
        raise SystemExit("Unexpected result payload (expected JSON object)")

    name = build_order_strategy_mock_name_from_upload_filename(
        strategy=strategy,
        upload_filename=upload_filename,
    )

    out = write_order_strategy_mock_text(
        name=name,
        text=json.dumps(payload, ensure_ascii=False, indent=2),
        overwrite=overwrite,
    )

    print(f"Recorded strategy mock: {out}")


if __name__ == "__main__":
    main()
