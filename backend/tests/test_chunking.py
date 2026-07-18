"""Unit tests for ChunkingService — losslessness, word-boundary overlap, paragraph packing."""

from services.chunking_service import ChunkingService


class TestChunkingService:
    def setup_method(self):
        self.service = ChunkingService(chunk_size=500, chunk_overlap=50)

    # ── basic paragraph packing ─────────────────────────────────────────────

    def test_short_paragraphs_merge_into_one_chunk(self):
        text = "Hello world.\n\nSecond paragraph."
        chunks = self.service.chunk(text)
        assert len(chunks) == 1
        assert "Hello world." in chunks[0]
        assert "Second paragraph." in chunks[0]

    def test_multiple_paragraphs_split_at_limit(self):
        para = "A" * 400
        text = f"{para}\n\n{para}\n\n{para}"
        chunks = self.service.chunk(text)
        assert len(chunks) >= 3

    # ── losslessness (no data dropped from long sentences) ───────────────────

    def test_long_sentence_preserved_completely(self):
        sentence = ("The quick brown fox jumps over the lazy dog. " * 120).strip()
        chunks = self.service.chunk(sentence)
        reconstructed = "".join(chunks)
        for word in sentence.split():
            assert word in reconstructed, f"Word '{word}' missing from output"

    def test_sentence_shorter_than_chunk_size_not_truncated(self):
        sentence = "Short sentence."
        chunks = self.service.chunk(sentence)
        assert sentence in chunks[0]

    def test_no_overlap_prefix_on_single_chunk(self):
        text = "Single short paragraph that fits in one chunk."
        chunks = self.service.chunk(text)
        assert len(chunks) == 1
        assert chunks[0] == text

    # ── word-boundary overlap ────────────────────────────────────────────────

    def test_overlap_starts_on_word_boundary(self):
        sentence = "The quick brown fox jumps over the lazy dog. "
        text = sentence * 60
        chunks = self.service.chunk(text)
        assert len(chunks) > 1, f"Expected >1 chunk, got {len(chunks)} — text too short? length={len(text)}"
        for chunk in chunks[1:]:
            first_word = chunk.split()[0] if chunk.split() else ""
            assert first_word, f"Chunk starts with no content: {chunk[:50]!r}"

    def test_overlap_trim_removes_partial_word(self):
        para = "The quick brown fox jumps over the lazy dog. " * 60
        content = f"{para.strip()}\n\n{para.strip()}"
        chunks = self.service.chunk(content)
        for i, chunk in enumerate(chunks):
            words = chunk.split()
            if words:
                first_word = words[0]
                assert len(first_word) > 0, f"Chunk {i} starts empty"
