from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from core.config import settings
from renderers.base import (
    BaseRenderer,
    RenderContext,
    RenderError,
    RendererUnavailableError,
    render_source,
)

_LATEX_ENABLE_HINT = (
    "LaTeX rendering is disabled. Set APP_PDF_LATEX_ENABLED=true and install a TeX "
    "distribution (e.g. texlive-latex-recommended + texlive-fonts-recommended) in the "
    "backend image to enable it."
)


class LatexRenderer(BaseRenderer):
    """Jinja2 LaTeX template → PDF via pdflatex subprocess.

    Stubbed by default: requires settings.pdf_latex_enabled and a TeX distribution
    in the runtime image. See ADR 0007.
    """

    name = "latex"

    def supported_outputs(self) -> list[str]:
        return ["pdf"]

    @staticmethod
    def availability() -> tuple[bool, str | None]:
        if not settings.pdf_latex_enabled:
            return False, _LATEX_ENABLE_HINT
        if shutil.which(settings.pdf_latex_command) is None:
            return (
                False,
                f"'{settings.pdf_latex_command}' not found on PATH; "
                "install a TeX distribution in the backend image.",
            )
        return True, None

    def render(self, ctx: RenderContext, output_format: str) -> bytes:
        if output_format != "pdf":
            raise RenderError(f"LaTeX templates cannot produce '{output_format}' output")
        available, reason = self.availability()
        if not available:
            raise RendererUnavailableError(reason)
        if not ctx.template_source.strip():
            raise RenderError("LaTeX template source is empty")

        source = render_source(ctx.template_source, ctx)

        with tempfile.TemporaryDirectory(prefix="latex-render-") as tmpdir:
            path = Path(tmpdir) / "resume.tex"
            path.write_text(source, encoding="utf-8")
            try:
                result = subprocess.run(
                    [
                        settings.pdf_latex_command,
                        "-interaction=nonstopmode",
                        "-halt-on-error",
                        f"-output-directory={tmpdir}",
                        str(path),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=settings.pdf_render_timeout_seconds,
                    check=False,
                )
            except subprocess.TimeoutExpired as e:
                raise RenderError(
                    f"pdflatex timed out after {settings.pdf_render_timeout_seconds}s"
                ) from e

            pdf_path = Path(tmpdir) / "resume.pdf"
            if result.returncode != 0 or not pdf_path.exists():
                log_tail = (result.stdout or result.stderr or "")[-1500:]
                raise RenderError(f"pdflatex failed:\n{log_tail}")
            return pdf_path.read_bytes()
