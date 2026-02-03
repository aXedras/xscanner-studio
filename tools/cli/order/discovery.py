"""Input discovery for order compare."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class OrderInputGroup:
    base: str
    pdf_text: Path | None
    pdf_image: Path | None
    images: list[Path]


def _base_from_stem(stem: str) -> str:
    return stem.removesuffix("-image")


def discover_order_input_groups(root_dir: Path) -> list[OrderInputGroup]:
    if not root_dir.exists():
        return []

    pdfs = sorted(root_dir.glob("*.pdf"))
    bases = sorted({_base_from_stem(p.stem) for p in pdfs})

    groups: list[OrderInputGroup] = []
    for base in bases:
        pdf_text = root_dir / f"{base}.pdf"
        pdf_image = root_dir / f"{base}-image.pdf"

        images: list[Path] = []
        for ext in ("*.jpg", "*.jpeg", "*.png"):
            images.extend(sorted(root_dir.glob(f"{base}*{ext[1:]}")))

        groups.append(
            OrderInputGroup(
                base=base,
                pdf_text=pdf_text if pdf_text.exists() else None,
                pdf_image=pdf_image if pdf_image.exists() else None,
                images=images,
            )
        )

    return groups
