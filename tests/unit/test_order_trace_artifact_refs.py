from __future__ import annotations

from dataclasses import dataclass

from xscanner.lib.trace_tree import TraceArtifact, TraceTree, iter_trace_spans
from xscanner.server.order.strategy import OrderStrategyChoice
from xscanner.server.order.workflow import textify as textify_module
from xscanner.server.order.workflow.textify import textify_input


def _find_artifacts(trace: TraceTree, *, key: str) -> list[TraceArtifact]:
    found: list[TraceArtifact] = []
    for sp in iter_trace_spans(trace.root):
        for art in sp.get("artifacts") or []:
            if art.get("key") == key:
                found.append(art)
    return found


def test_textify_pdf_text_artifact_is_ref_only(monkeypatch) -> None:
    expected_text = "X" * 1200

    def _fake_extract_text_from_pdf_bytes(_: bytes) -> str:
        return expected_text

    def _fake_text_quality_gate(_: str):
        from xscanner.server.order.processing.text_quality_gate import TextQualityMetrics

        return "good", TextQualityMetrics(
            char_count=1200,
            line_count=10,
            gibberish_ratio=0.0,
            anchor_hits=5,
        )

    monkeypatch.setattr(
        textify_module, "extract_text_from_pdf_bytes", _fake_extract_text_from_pdf_bytes
    )
    monkeypatch.setattr(textify_module, "text_quality_gate", _fake_text_quality_gate)

    trace = TraceTree.start(name="test.trace")
    result = textify_input(
        pdf_bytes=b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF\n",
        page_images=None,
        strategy=OrderStrategyChoice.manual,
        trace=trace,
    )

    assert result.success is True
    assert result.textify_mode == "pdf_text"
    assert result.raw_text == expected_text

    artifacts = _find_artifacts(trace, key="input.textify.pdf_text")
    assert len(artifacts) == 1

    art = artifacts[0]
    assert art.get("ref") == "extracted_data.raw.pdf_text"
    assert "value" not in art


def test_textify_vision_marker_text_artifact_is_ref_only(monkeypatch) -> None:
    @dataclass(frozen=True)
    class _FakeMarker:
        marker_text: str
        provider: str
        model: str
        usage: dict

    expected_marker_text = "__HEADER__\nHello\n"

    def _fake_run_order_vision_to_marker_text(*, page_images, trace):
        assert len(page_images) == 1
        assert trace is not None
        return _FakeMarker(
            marker_text=expected_marker_text,
            provider="test",
            model="test",
            usage={},
        )

    monkeypatch.setattr(
        textify_module, "run_order_vision_to_marker_text", _fake_run_order_vision_to_marker_text
    )

    trace = TraceTree.start(name="test.trace")
    result = textify_input(
        pdf_bytes=None,
        page_images=[b"fake-image-bytes"],
        strategy=OrderStrategyChoice.manual,
        trace=trace,
    )

    assert result.success is True
    assert result.textify_mode == "vision_marker_text"
    assert result.raw_text == expected_marker_text

    artifacts = _find_artifacts(trace, key="input.textify.marker_text")
    assert len(artifacts) == 1

    art = artifacts[0]
    assert art.get("ref") == "extracted_data.raw.marker_text"
    assert "value" not in art
