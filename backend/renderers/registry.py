from __future__ import annotations

from typing import Any

from renderers.base import BaseRenderer
from renderers.docx_renderer import DocxRenderer
from renderers.html_renderer import HtmlRenderer
from renderers.latex_renderer import LatexRenderer
from renderers.typst_renderer import TypstRenderer

_RENDERERS: dict[str, BaseRenderer] = {
    "html": HtmlRenderer(),
    "typst": TypstRenderer(),
    "latex": LatexRenderer(),
    "docx": DocxRenderer(),
}


def template_formats() -> list[str]:
    return list(_RENDERERS)


def get_renderer(template_format: str) -> BaseRenderer:
    renderer = _RENDERERS.get(template_format.lower())
    if renderer is None:
        raise ValueError(
            f"Unknown template format '{template_format}'. "
            f"Supported: {', '.join(_RENDERERS)}"
        )
    return renderer


def resolve_engine(template_format: str, output_format: str) -> str:
    """Human-readable engine label for a template-format → output-format pair."""
    renderer = get_renderer(template_format)
    if output_format not in renderer.supported_outputs():
        raise ValueError(
            f"Template format '{template_format}' cannot produce '{output_format}' output"
        )
    if template_format == "docx" and output_format == "pdf":
        return "docx+libreoffice"
    return renderer.name


def capabilities() -> list[dict[str, Any]]:
    """Capability report for all template formats / output formats."""
    report: list[dict[str, Any]] = []
    for template_format, renderer in _RENDERERS.items():
        if template_format == "latex":
            available, reason = LatexRenderer.availability()
            report.append(
                {
                    "format": template_format,
                    "engine": renderer.name,
                    "output": "pdf",
                    "available": available,
                    "reason": reason,
                }
            )
            continue
        if template_format == "docx":
            report.append(
                {
                    "format": template_format,
                    "engine": renderer.name,
                    "output": "docx",
                    "available": True,
                    "reason": None,
                }
            )
            soffice = DocxRenderer.soffice_available()
            report.append(
                {
                    "format": template_format,
                    "engine": "docx+libreoffice",
                    "output": "pdf",
                    "available": soffice,
                    "reason": None if soffice else "LibreOffice (soffice) not found on PATH",
                }
            )
            continue
        report.append(
            {
                "format": template_format,
                "engine": renderer.name,
                "output": "pdf",
                "available": True,
                "reason": None,
            }
        )
    return report
