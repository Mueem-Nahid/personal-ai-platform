from __future__ import annotations

import io

import pdfplumber
from docx import Document as DocxDocument


class ExtractionService:
    @staticmethod
    def extract(data: bytes, file_type: str) -> str:
        ext = file_type.lower()
        if ext in ("pdf",):
            return ExtractionService._extract_pdf(data)
        elif ext in ("docx", "doc"):
            return ExtractionService._extract_docx(data)
        elif ext in ("txt", "md", "text", "markdown"):
            return data.decode("utf-8", errors="replace")
        else:
            return data.decode("utf-8", errors="replace")

    @staticmethod
    def _extract_pdf(data: bytes) -> str:
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
        return "\n\n".join(pages)

    @staticmethod
    def _extract_docx(data: bytes) -> str:
        doc = DocxDocument(io.BytesIO(data))
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        return "\n\n".join(paragraphs)
