from __future__ import annotations

import re


class ChunkingService:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50) -> None:
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    def chunk(self, text: str) -> list[str]:
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        chunks: list[str] = []
        current = ""

        for para in paragraphs:
            if len(current) + len(para) <= self._chunk_size:
                current = f"{current}\n\n{para}" if current else para
            else:
                if len(para) > self._chunk_size:
                    if current:
                        chunks.append(current)
                    chunks.extend(self._split_long_paragraph(para))
                    current = ""
                else:
                    chunks.append(current)
                    current = para

        if current:
            chunks.append(current)

        # apply overlap by prefixing each chunk with tail of previous
        if self._chunk_overlap > 0 and len(chunks) > 1:
            overlapped = [chunks[0]]
            for i in range(1, len(chunks)):
                prev = overlapped[-1]
                tail = prev[-self._chunk_overlap:] if len(prev) > self._chunk_overlap else prev
                space = tail.find(" ")
                if space > 0:
                    tail = tail[space + 1:]
                overlapped.append(f"{tail}\n{chunks[i]}")
            return overlapped

        return chunks

    def _split_long_paragraph(self, text: str) -> list[str]:
        sentences = re.split(r"(?<=[.!?])\s+", text)
        chunks: list[str] = []
        current = ""
        for sentence in sentences:
            while len(sentence) > self._chunk_size:
                if current:
                    chunks.append(current)
                    current = ""
                cut = sentence.rfind(" ", 0, self._chunk_size)
                if cut <= 0:
                    cut = self._chunk_size
                chunks.append(sentence[:cut])
                sentence = sentence[cut:].lstrip()
            if len(current) + len(sentence) <= self._chunk_size:
                current = f"{current} {sentence}" if current else sentence
            else:
                if current:
                    chunks.append(current)
                current = sentence
        if current:
            chunks.append(current)
        return chunks
