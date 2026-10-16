from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from jinja2 import ChainableUndefined
from jinja2.sandbox import SandboxedEnvironment

from schemas.resume import ResumeContent


class RenderError(Exception):
    """Raised when a renderer fails to produce output."""


class RendererUnavailableError(RenderError):
    """Raised when the renderer's toolchain is not installed or not enabled."""


@dataclass
class RenderContext:
    """Everything a renderer needs to turn content + template into a document."""

    content: ResumeContent
    profile: dict[str, Any] = field(default_factory=dict)
    job: dict[str, str] = field(default_factory=dict)
    template_source: str = ""
    styles_text: str | None = None
    template_asset: bytes | None = None


def build_jinja_env(autoescape: bool = False) -> SandboxedEnvironment:
    """Sandboxed Jinja2 environment for user-editable template sources."""
    env = SandboxedEnvironment(
        autoescape=autoescape,
        undefined=ChainableUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    env.filters["latex"] = latex_escape
    env.filters["typst"] = typst_escape
    return env


def latex_escape(value: Any) -> str:
    text = "" if value is None else str(value)
    replacements = [
        ("\\", r"\textbackslash{}"),
        ("&", r"\&"),
        ("%", r"\%"),
        ("$", r"\$"),
        ("#", r"\#"),
        ("_", r"\_"),
        ("{", r"\{"),
        ("}", r"\}"),
        ("~", r"\textasciitilde{}"),
        ("^", r"\textasciicircum{}"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def typst_escape(value: Any) -> str:
    text = "" if value is None else str(value)
    replacements = [
        ("\\", r"\\"),
        ("#", r"\#"),
        ("$", r"\$"),
        ("[", r"\["),
        ("]", r"\]"),
        ("<", r"\<"),
        (">", r"\>"),
        ("@", r"\@"),
        ("*", r"\*"),
        ("_", r"\_"),
        ("`", r"\`"),
        ("~", r"\~"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def render_source(source: str, ctx: RenderContext, autoescape: bool = False) -> str:
    """Render template source with the standard context (profile/content/job).

    The ResumeContent model is passed as-is (attribute access) so that
    `section.items` is the field, not the dict method.
    """
    env = build_jinja_env(autoescape=autoescape)
    template = env.from_string(source)
    return template.render(
        profile=ctx.profile or {},
        content=ctx.content,
        job=ctx.job or {},
    )


class BaseRenderer(ABC):
    """Turns resume content plus a template into an output document."""

    name: str = "base"

    @abstractmethod
    def supported_outputs(self) -> list[str]:
        """Output formats this renderer can produce (e.g. ['pdf'])."""

    @abstractmethod
    def render(self, ctx: RenderContext, output_format: str) -> bytes:
        """Produce the document bytes; raises RenderError on failure."""
