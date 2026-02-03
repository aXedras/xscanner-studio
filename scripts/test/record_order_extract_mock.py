"""Record a real cloud extract response as a deterministic mock fixture.

This script calls the real AI provider (OpenAI) and stores the raw JSON envelope
(meta/raw/structured_data) so we can run `use_mock=true` without external calls.

Usage (from repo root):
    venv/bin/python scripts/test/record_order_extract_mock.py --file invoices/72056547.pdf

Requires:
  - OPENAI_API_KEY set

Output:
    - writes src/xscanner/mockdata/order_extract/<name>.json

Notes:
  - If --name is omitted, the fixture name is derived from the PDF filename
    (must match the upload filename the client sends).
    - Recording always overwrites an existing fixture.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from xscanner.mockdata.order_extract import (
    build_order_extract_mock_name_from_upload_filename,
    write_order_extract_mock_text,
)
from xscanner.server.order.ai.runner import run_order_extraction_via_ai
from xscanner.server.order.processing.document_detection import OrderDocumentDetection
from xscanner.server.order.processing.marker_text import build_marker_text
from xscanner.server.order.processing.pdf_text import extract_text_from_pdf_bytes
from xscanner.server.order.processing.pipeline import run_preprocessing
from xscanner.server.order.processing.raw_signals import extract_raw_order_data


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--file", required=False, default=None, help="Path to sample PDF/JPG")
    p.add_argument(
        "--name",
        required=False,
        default=None,
        help=(
            "Fixture name (writes src/xscanner/mockdata/order_extract/<name>.json). "
            "If omitted, the name is derived deterministically from the PDF filename."
        ),
    )
    args = p.parse_args()
    if not args.file:
        raise SystemExit("Missing required argument: --file <path>")
    return args


def main() -> None:
    args = _parse_args()

    input_path = args.file
    with open(input_path, "rb") as f:
        pdf_bytes = f.read()

    upload_filename = Path(input_path).name
    name = args.name or build_order_extract_mock_name_from_upload_filename(
        upload_filename=upload_filename
    )

    raw_text = extract_text_from_pdf_bytes(pdf_bytes)

    detector = OrderDocumentDetection()
    initial = detector.detect(raw_text)
    issuer = initial.document_issuer
    if issuer == "unknown":
        raise SystemExit("Could not detect issuer from PDF text")

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

    # Persist the AI envelope, augmented with usage metadata so recorded mocks can replay
    # provider/model/token counts without an external API call.
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

    text_to_store = json.dumps(envelope, ensure_ascii=False, indent=2)

    out_path = write_order_extract_mock_text(
        name=name,
        text=text_to_store,
        overwrite=True,
    )

    print(f"Recorded AI mock saved: {out_path}")
    print(f"Fixture name: {name}")


if __name__ == "__main__":
    main()
