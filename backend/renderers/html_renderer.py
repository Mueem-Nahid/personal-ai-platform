from __future__ import annotations

from typing import Any

from renderers.base import (
    BaseRenderer,
    RenderContext,
    RenderError,
    RendererUnavailableError,
    render_source,
)


def _load_weasyprint_html() -> Any:
    try:
        from weasyprint import HTML
    except Exception as e:
        raise RendererUnavailableError(
            "WeasyPrint unavailable. HTML PDF rendering requires Pango and its native "
            "libraries. On Windows, install MSYS2 and run "
            "'pacman -S mingw-w64-ucrt-x86_64-pango' in its UCRT64 shell, then restart "
            "the backend and ARQ worker. If Windows Application Control blocks the "
            "DLLs, use the Docker worker or a Typst template. "
            f"Details: {e}"
        ) from e
    return HTML


def _inject_styles(html: str, styles: str) -> str:
    """Inject CSS into the document head (or body/html start as fallback)."""
    block = f"<style>\n{styles}\n</style>"
    if "</head>" in html:
        return html.replace("</head>", f"{block}\n</head>", 1)
    if "<body" in html:
        head, sep, tail = html.partition("<body")
        tag_end = tail.find(">")
        if tag_end != -1:
            return f"{head}{sep}{tail[: tag_end + 1]}\n{block}{tail[tag_end + 1 :]}"
    return f"{block}\n{html}"


class HtmlRenderer(BaseRenderer):
    """Jinja2 HTML template + CSS → PDF via WeasyPrint."""

    name = "weasyprint"

    @staticmethod
    def availability() -> tuple[bool, str | None]:
        try:
            _load_weasyprint_html()
        except RendererUnavailableError as e:
            return False, str(e)
        return True, None

    def supported_outputs(self) -> list[str]:
        return ["pdf"]

    def render(self, ctx: RenderContext, output_format: str) -> bytes:
        if output_format != "pdf":
            raise RenderError(f"HTML templates cannot produce '{output_format}' output")
        if not ctx.template_source.strip():
            raise RenderError("HTML template source is empty")

        html = render_source(ctx.template_source, ctx, autoescape=True)
        if ctx.styles_text and ctx.styles_text.strip():
            html = _inject_styles(html, ctx.styles_text)

        HTML = _load_weasyprint_html()

        try:
            pdf: bytes = HTML(string=html).write_pdf()
            return pdf
        except RendererUnavailableError:
            raise
        except Exception as e:
            raise RenderError(f"WeasyPrint render failed: {e}") from e
