# ADR 0007 — PDF Engine Renderer Choices

## Status

Accepted

## Context

Phase 6 requires converting structured resume content (`resume_versions.content_json`) plus user-editable templates into PDF/DOCX documents, and importing existing resume PDFs back into editable content. The roadmap requires support for HTML (Jinja2 + WeasyPrint), LaTeX, Typst, and DOCX, plus PDF import.

Constraints:

- **Local-first**: rendering must be fully offline; no SaaS document APIs.
- **User-editable templates**: template sources are user input and must be sandboxed.
- **Docker image weight**: the backend image must not balloon (the full stack already ships Ollama).
- **Async pipeline**: rendering follows the established ARQ background-job pattern (Phases 3–5).

## Decision

### Renderer abstraction

`backend/renderers/` exposes `BaseRenderer.render(ctx, output_format)` behind a registry (`renderers/registry.py`) that also reports a capability matrix (`format × output × available`) so the API can fail fast with actionable errors (e.g. LaTeX disabled).

| Format | Engine | Outputs | Notes |
|---|---|---|---|
| HTML | Jinja2 (sandboxed) → WeasyPrint | pdf | CSS injected from `styles_text`; primary path, ships in base image |
| Typst | Jinja2 (sandboxed) → `typst` pip package | pdf | Compiler bundled in wheel — zero system dependencies |
| DOCX | python-docx | docx, pdf (via LibreOffice headless) | Fills `{{ }}` placeholders in uploaded .docx, or builds programmatically |
| LaTeX | Jinja2 (sandboxed) → `pdflatex` subprocess | pdf | **Stubbed**: requires `APP_PDF_LATEX_ENABLED=true` + texlive in image |

Templates are rendered through `jinja2.sandbox.SandboxedEnvironment` with `ChainableUndefined` (missing fields render empty rather than crashing). `latex`/`typst` escape filters are registered for source-format-specific escaping.

### LaTeX: stubbed, not shipped

A usable TeX distribution (texlive-latex-recommended + fonts) adds ~700MB to the image for a format that is optional for this workflow. The renderer is fully implemented and gated behind `APP_PDF_LATEX_ENABLED` (default `false`) plus a `shutil.which("pdflatex")` probe; enabling requires only image changes documented in `infrastructure/docker/backend.Dockerfile`.

### DOCX→PDF via LibreOffice headless

LibreOffice is the only credible local DOCX→PDF converter. It runs as `soffice --headless --convert-to pdf` with a per-invocation `-env:UserInstallation` profile directory (avoids concurrent-run profile corruption) and a configurable timeout. Renders run inside `asyncio.to_thread` so workers stay responsive.

### PDF import: extract → re-render, not layout preservation

True PDF→editable-template conversion is research-grade. Instead, `renderers/pdf_import.py` uses pdfplumber to extract lines with font sizes and applies heuristics: largest text → name, known heading names / relative font size → section boundaries, bullet glyphs → items, wrapped non-bullet lines merge into the previous item, contact lines near the top are captured separately. The result is a `ResumeContent` re-renderable through any template. Scanned/image PDFs are rejected with a clear error.

### Data model

- `resume_templates`: text sources (`source_text`, `styles_text`) or binary asset (`asset_key` → MinIO `templates/` prefix), per-profile or built-in (`builtin_key`, seeded at startup — insert-only, so user edits to built-ins survive restarts; shipping a changed built-in requires bumping its key).
- Default semantics: a profile-scoped default *overrides* the global built-in default but never erases it; `resume_jobs.template_id` and `resume_version_id` are `SET NULL` on delete so render history (and its MinIO artifacts) survives version/template deletion.
- `render_jobs`: ARQ-tracked jobs with a `content_json` snapshot (reproducible renders even if the version is later edited), MinIO output key, engine label, and stale-sweeping like prior phases.

## Consequences

- **Image size**: LibreOffice + fonts add ~400MB to backend/worker images. Acceptable for a local-first platform; only these two images grow.
- **Template power**: Jinja2 sandboxing prevents template escape; DOCX templates support scalar placeholders only (no `{% for %}` across Word paragraphs) — documented limitation.
- **Typst fidelity**: content text is escaped through `|typst` (emails' `@`, `$`, `#`, etc.) so arbitrary resume text cannot inject Typst code.
- **PDF import fidelity**: layout is approximated, not preserved; complex multi-column PDFs may mis-segment. This matches the "editable re-render" goal.

## Alternatives Considered

1. **wkhtmltopdf** — abandoned upstream, worse CSS fidelity than WeasyPrint.
2. **ReportLab/FPDF programmatic PDF** — no user-editable template story.
3. **Pandoc for LaTeX/Typst** — extra system dependency chain, GPL complexities with templates.
4. **pdf2docx / layout-preserving PDF import** — poor quality on real resumes; deferred.
5. **Shipping texlive now** — image weight for an optional format; deferred until requested.
