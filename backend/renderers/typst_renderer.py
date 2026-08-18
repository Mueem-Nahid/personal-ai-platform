from __future__ import annotations

import tempfile
from pathlib import Path

from renderers.base import (
    BaseRenderer,
    RenderContext,
    RenderError,
    render_source,
)


class TypstRenderer(BaseRenderer):
    """Jinja2 Typst template → PDF via the typst compiler (pip package)."""

    name = "typst"

    def supported_outputs(self) -> list[str]:
        return ["pdf"]

    def render(self, ctx: RenderContext, output_format: str) -> bytes:
        if output_format != "pdf":
            raise RenderError(f"Typst templates cannot produce '{output_format}' output")
        if not ctx.template_source.strip():
            raise RenderError("Typst template source is empty")

        try:
            import typst
        except Exception as e:  # pragma: no cover - import failures are env issues
            raise RenderError(f"typst package unavailable: {e}") from e

        source = render_source(ctx.template_source, ctx)

        try:
            with tempfile.TemporaryDirectory(prefix="typst-render-") as tmpdir:
                path = Path(tmpdir) / "resume.typ"
                path.write_text(source, encoding="utf-8")
                return typst.compile(str(path))
        except Exception as e:
            raise RenderError(f"Typst compile failed: {e}") from e
