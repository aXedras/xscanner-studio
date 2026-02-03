"""Order compare flow.

This is a developer tool that runs the order extraction service for a chosen
"base" document (e.g. 72056547) and compares strategies.

Important: this intentionally does not normalize values.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from xscanner.mockdata.order_strategy import (
    build_order_strategy_mock_name_from_upload_filename,
    read_order_strategy_mock_text,
    write_order_strategy_mock_text,
)
from xscanner.server.order.service import get_order_extraction_service
from xscanner.server.order.strategy import OrderStrategyChoice

from .diff import iter_diff_paths
from .discovery import OrderInputGroup, discover_order_input_groups
from .report import build_order_compare_html


@dataclass(frozen=True)
class RunResult:
    ok: bool
    payload: dict[str, Any] | None
    error: str | None
    processing_time_s: float | None
    source: str
    fixture_name: str | None


def _prompt_confirm_overwrite() -> bool:
    while True:
        raw = input("⚠️  Fixtures überschreiben und neu extrahieren? (y/N): ").strip().lower()
        if raw in {"", "n", "no"}:
            return False
        if raw in {"y", "yes"}:
            return True
        print("Bitte 'y' oder 'n' eingeben.")


def _normalize_image_to_png_bytes(img_bytes: bytes) -> bytes:
    from io import BytesIO

    from PIL import Image

    with Image.open(BytesIO(img_bytes)) as im:
        converted = im.convert("RGB")
        buf = BytesIO()
        converted.save(buf, format="PNG")
        return buf.getvalue()


def _run_on_pdf(path: Path, *, strategy: OrderStrategyChoice) -> RunResult:
    service = get_order_extraction_service()
    # Use debug=True when recording fixtures so we keep the full envelope
    # (e.g. raw_text) for later analysis.
    res = service.extract(
        pdf_bytes=path.read_bytes(), page_images=None, strategy=strategy, debug=True
    )

    if not res.success:
        return RunResult(
            ok=False,
            payload=None,
            error=res.error or "Unknown error",
            processing_time_s=res.processing_time,
            source="live",
            fixture_name=None,
        )

    payload: Any
    if hasattr(res.result, "model_dump"):
        payload = res.result.model_dump()
    else:
        payload = res.result

    if not isinstance(payload, dict):
        return RunResult(
            ok=False,
            payload=None,
            error="Unexpected result payload (expected object)",
            processing_time_s=res.processing_time,
            source="live",
            fixture_name=None,
        )

    return RunResult(
        ok=True,
        payload=payload,
        error=None,
        processing_time_s=res.processing_time,
        source="live",
        fixture_name=None,
    )


def _run_on_images(paths: list[Path], *, strategy: OrderStrategyChoice) -> RunResult:
    service = get_order_extraction_service()

    raws = [p.read_bytes() for p in paths]
    page_images = [_normalize_image_to_png_bytes(b) for b in raws]

    # Use debug=True when recording fixtures so we keep the full envelope
    # (e.g. raw_text) for later analysis.
    res = service.extract(pdf_bytes=None, page_images=page_images, strategy=strategy, debug=True)

    if not res.success:
        return RunResult(
            ok=False,
            payload=None,
            error=res.error or "Unknown error",
            processing_time_s=res.processing_time,
            source="live",
            fixture_name=None,
        )

    payload: Any
    if hasattr(res.result, "model_dump"):
        payload = res.result.model_dump()
    else:
        payload = res.result

    if not isinstance(payload, dict):
        return RunResult(
            ok=False,
            payload=None,
            error="Unexpected result payload (expected object)",
            processing_time_s=res.processing_time,
            source="live",
            fixture_name=None,
        )

    return RunResult(
        ok=True,
        payload=payload,
        error=None,
        processing_time_s=res.processing_time,
        source="live",
        fixture_name=None,
    )


def _load_strategy_fixture(
    *, strategy: OrderStrategyChoice, upload_filename: str
) -> dict[str, Any] | None:
    name = build_order_strategy_mock_name_from_upload_filename(
        strategy=strategy,
        upload_filename=upload_filename,
    )
    txt = read_order_strategy_mock_text(name)
    if not txt:
        return None
    parsed = json.loads(txt)
    if not isinstance(parsed, dict):
        raise RuntimeError(f"Invalid fixture payload (expected object): {name}")
    return parsed


def _record_strategy_fixture(
    *,
    strategy: OrderStrategyChoice,
    upload_filename: str,
    payload: dict[str, Any],
    overwrite: bool,
) -> str:
    name = build_order_strategy_mock_name_from_upload_filename(
        strategy=strategy,
        upload_filename=upload_filename,
    )
    write_order_strategy_mock_text(
        name=name,
        text=json.dumps(payload, ensure_ascii=False, indent=2),
        overwrite=overwrite,
    )
    return name


def _get_or_run_pdf(
    *,
    path: Path,
    strategy: OrderStrategyChoice,
    fixtures_only: bool,
    refresh_fixtures: bool,
) -> RunResult:
    upload_filename = path.name
    try:
        fixture = _load_strategy_fixture(strategy=strategy, upload_filename=upload_filename)
    except Exception as e:
        return RunResult(
            ok=False,
            payload=None,
            error=f"Failed to read fixture: {e}",
            processing_time_s=None,
            source="fixture",
            fixture_name=None,
        )

    if fixture is not None and not refresh_fixtures:
        name = build_order_strategy_mock_name_from_upload_filename(
            strategy=strategy,
            upload_filename=upload_filename,
        )
        return RunResult(
            ok=True,
            payload=fixture,
            error=None,
            processing_time_s=None,
            source="fixture",
            fixture_name=name,
        )

    if fixtures_only:
        missing = build_order_strategy_mock_name_from_upload_filename(
            strategy=strategy,
            upload_filename=upload_filename,
        )
        return RunResult(
            ok=False,
            payload=None,
            error=(
                f"Missing fixture (fixtures-only): {missing}"
                if fixture is None
                else f"Refresh requested but fixtures-only is set: {missing}"
            ),
            processing_time_s=None,
            source="fixture",
            fixture_name=missing,
        )

    live = _run_on_pdf(path, strategy=strategy)
    if live.ok and live.payload is not None:
        try:
            name = _record_strategy_fixture(
                strategy=strategy,
                upload_filename=upload_filename,
                payload=live.payload,
                overwrite=fixture is not None,
            )
            return RunResult(
                ok=True,
                payload=live.payload,
                error=None,
                processing_time_s=live.processing_time_s,
                source="live+recorded" if fixture is None else "live+overwritten",
                fixture_name=name,
            )
        except Exception as e:
            return RunResult(
                ok=False,
                payload=None,
                error=f"Live extraction succeeded, but recording fixture failed: {e}",
                processing_time_s=live.processing_time_s,
                source="live",
                fixture_name=None,
            )

    return live


def _get_or_run_images(
    *,
    paths: list[Path],
    strategy: OrderStrategyChoice,
    fixtures_only: bool,
    refresh_fixtures: bool,
) -> RunResult:
    if not paths:
        return RunResult(
            ok=False,
            payload=None,
            error="No image paths",
            processing_time_s=None,
            source="input",
            fixture_name=None,
        )

    upload_filename = paths[0].name
    try:
        fixture = _load_strategy_fixture(strategy=strategy, upload_filename=upload_filename)
    except Exception as e:
        return RunResult(
            ok=False,
            payload=None,
            error=f"Failed to read fixture: {e}",
            processing_time_s=None,
            source="fixture",
            fixture_name=None,
        )

    if fixture is not None and not refresh_fixtures:
        name = build_order_strategy_mock_name_from_upload_filename(
            strategy=strategy,
            upload_filename=upload_filename,
        )
        return RunResult(
            ok=True,
            payload=fixture,
            error=None,
            processing_time_s=None,
            source="fixture",
            fixture_name=name,
        )

    if fixtures_only:
        missing = build_order_strategy_mock_name_from_upload_filename(
            strategy=strategy,
            upload_filename=upload_filename,
        )
        return RunResult(
            ok=False,
            payload=None,
            error=(
                f"Missing fixture (fixtures-only): {missing}"
                if fixture is None
                else f"Refresh requested but fixtures-only is set: {missing}"
            ),
            processing_time_s=None,
            source="fixture",
            fixture_name=missing,
        )

    live = _run_on_images(paths, strategy=strategy)
    if live.ok and live.payload is not None:
        try:
            name = _record_strategy_fixture(
                strategy=strategy,
                upload_filename=upload_filename,
                payload=live.payload,
                overwrite=fixture is not None,
            )
            return RunResult(
                ok=True,
                payload=live.payload,
                error=None,
                processing_time_s=live.processing_time_s,
                source="live+recorded" if fixture is None else "live+overwritten",
                fixture_name=name,
            )
        except Exception as e:
            return RunResult(
                ok=False,
                payload=None,
                error=f"Live extraction succeeded, but recording fixture failed: {e}",
                processing_time_s=live.processing_time_s,
                source="live",
                fixture_name=None,
            )

    return live


def _structured_data(payload: dict[str, Any]) -> dict[str, Any]:
    value = payload.get("structured_data")
    return value if isinstance(value, dict) else {}


def _pick_group_interactive(groups: list[OrderInputGroup]) -> OrderInputGroup:
    print("\n📄 Gefundene Order-PDFs:\n")
    for idx, g in enumerate(groups, 1):
        flags = []
        if g.pdf_text is not None:
            flags.append("pdf")
        if g.pdf_image is not None:
            flags.append("image-pdf")
        if g.images:
            flags.append(f"images={len(g.images)}")
        extra = f" ({', '.join(flags)})" if flags else ""
        print(f"  {idx}. {g.base}{extra}")

    while True:
        raw = input("\n🔢 Auswahl: ").strip()
        try:
            i = int(raw)
        except ValueError:
            i = -1
        if 1 <= i <= len(groups):
            return groups[i - 1]
        print("❌ Ungültige Auswahl")


def compare_interactive(
    *,
    root_dir: Path,
    base: str | None,
    max_diffs: int,
    output_path: Path | None,
    fixtures_only: bool = False,
    write_html: bool = True,
    refresh_fixtures: bool = False,
    assume_yes: bool = False,
) -> int:
    groups = discover_order_input_groups(root_dir)
    if not groups:
        print(f"❌ Keine PDFs gefunden in: {root_dir}")
        return 1

    group: OrderInputGroup
    was_interactive_base_pick = False
    if base:
        found = next((g for g in groups if g.base == base), None)
        if found is None:
            print(f"❌ Base nicht gefunden: {base}")
            return 1
        group = found
    else:
        was_interactive_base_pick = True
        group = _pick_group_interactive(groups)

    if group.pdf_text is None:
        print(f"❌ Für manual brauche ich {group.base}.pdf, aber die Datei fehlt.")
        return 1

    print(f"\n▶️  Compare: {group.base}")

    if refresh_fixtures and fixtures_only:
        print("❌ refresh-fixtures geht nicht zusammen mit --fixtures-only")
        return 2

    confirmed_refresh = False

    # Interactive UX: allow choosing refresh/overwrite without requiring flags.
    # Default remains fixture-first (no refresh) to avoid accidental API calls.
    if was_interactive_base_pick and not fixtures_only and not refresh_fixtures:
        if _prompt_confirm_overwrite():
            refresh_fixtures = True
            confirmed_refresh = True

    if refresh_fixtures and not assume_yes and not confirmed_refresh:
        if not _prompt_confirm_overwrite():
            print("✅ Abgebrochen (keine Fixtures überschrieben).")
            return 0

    manual_res = _get_or_run_pdf(
        path=group.pdf_text,
        strategy=OrderStrategyChoice.manual,
        fixtures_only=fixtures_only,
        refresh_fixtures=refresh_fixtures,
    )
    if not manual_res.ok or manual_res.payload is None:
        print(f"❌ Manual fehlgeschlagen: {manual_res.error}")
        return 1

    baseline_structured = _structured_data(manual_res.payload)

    cases: list[tuple[str, str, RunResult]] = []

    if group.pdf_text is not None:
        cases.append(
            (
                "cloud",
                group.pdf_text.name,
                _get_or_run_pdf(
                    path=group.pdf_text,
                    strategy=OrderStrategyChoice.cloud,
                    fixtures_only=fixtures_only,
                    refresh_fixtures=refresh_fixtures,
                ),
            )
        )
    if group.pdf_image is not None:
        cases.append(
            (
                "cloud",
                group.pdf_image.name,
                _get_or_run_pdf(
                    path=group.pdf_image,
                    strategy=OrderStrategyChoice.cloud,
                    fixtures_only=fixtures_only,
                    refresh_fixtures=refresh_fixtures,
                ),
            )
        )
    if group.images:
        label = "+".join(p.name for p in group.images)
        cases.append(
            (
                "cloud",
                label,
                _get_or_run_images(
                    paths=group.images,
                    strategy=OrderStrategyChoice.cloud,
                    fixtures_only=fixtures_only,
                    refresh_fixtures=refresh_fixtures,
                ),
            )
        )

    results_out: dict[str, Any] = {
        "base": group.base,
        "root_dir": str(root_dir),
        "timestamp": datetime.now().isoformat(),
        "baseline": {
            "strategy": "manual",
            "file": group.pdf_text.name,
            "ok": True,
            "processing_time_s": manual_res.processing_time_s,
            "source": manual_res.source,
            "fixture_name": manual_res.fixture_name,
            "envelope": manual_res.payload,
        },
        "comparisons": [],
    }

    print("\n📊 Diffs (raw structured_data):")

    for strategy_name, file_label, r in cases:
        entry: dict[str, Any] = {
            "strategy": strategy_name,
            "input": file_label,
            "ok": bool(r.ok),
            "processing_time_s": r.processing_time_s,
            "source": r.source,
            "fixture_name": r.fixture_name,
            "error": r.error,
            "envelope": r.payload,
            "diff": None,
        }

        if r.ok and r.payload is not None:
            right = _structured_data(r.payload)
            diffs = list(iter_diff_paths(baseline_structured, right))
            limited = diffs[: max(0, int(max_diffs))]
            entry["diff"] = {
                "count": len(diffs),
                "max_diffs": max_diffs,
                "entries": [{"path": d.path, "left": d.left, "right": d.right} for d in limited],
            }

            src = r.source
            note = f" [{src}]" if src else ""
            print(f"- cloud vs manual ({file_label}): {len(diffs)} diff(s){note}")
        else:
            print(f"- cloud ({file_label}): ❌ {r.error}")

        results_out["comparisons"].append(entry)

    out_dir = Path("reports/order")
    out_dir.mkdir(parents=True, exist_ok=True)
    if output_path is None:
        output_path = out_dir / f"compare_{group.base}.json"

    output_path.write_text(json.dumps(results_out, ensure_ascii=False, indent=2), encoding="utf-8")

    html_path = out_dir / f"compare_{group.base}.html"
    if write_html:
        html_path.write_text(build_order_compare_html(results_out), encoding="utf-8")

    print(f"\n✅ Report JSON: {output_path}")
    if write_html:
        print(f"✅ Report HTML: {html_path}")
    return 0
