from datetime import datetime

from src.ingestion.chunker import chunk_document, raw_to_document
from src.models.document import Document, RawDocument


def _make_document(content: str, doc_id: str = "test-doc") -> Document:
    return Document(
        id=doc_id,
        source_type="test",
        source_id="test-1",
        title="Test Document",
        content=content,
        timestamp=datetime(2024, 1, 15),
    )


class TestRawToDocument:
    def test_creates_document_with_stable_id(self):
        raw = RawDocument(
            source_type="gmail",
            source_id="msg123",
            title="Test",
            content="Hello",
            timestamp=datetime(2024, 1, 15),
        )
        doc = raw_to_document(raw)
        assert doc.id is not None
        assert doc.source_type == "gmail"
        assert doc.content == "Hello"

        # Same input should produce same ID
        doc2 = raw_to_document(raw)
        assert doc.id == doc2.id

    def test_different_sources_produce_different_ids(self):
        raw1 = RawDocument(
            source_type="gmail",
            source_id="msg1",
            title="A",
            content="x",
            timestamp=datetime(2024, 1, 15),
        )
        raw2 = RawDocument(
            source_type="gmail",
            source_id="msg2",
            title="B",
            content="y",
            timestamp=datetime(2024, 1, 15),
        )
        assert raw_to_document(raw1).id != raw_to_document(raw2).id


class TestChunkDocument:
    def test_short_text_single_chunk(self):
        doc = _make_document("Short text.")
        chunks = chunk_document(doc, chunk_size=512)
        assert len(chunks) == 1
        assert chunks[0].content == "Short text."
        assert chunks[0].document_id == doc.id
        assert chunks[0].index == 0

    def test_empty_content_no_chunks(self):
        doc = _make_document("")
        chunks = chunk_document(doc, chunk_size=512)
        assert chunks == []

    def test_whitespace_only_no_chunks(self):
        doc = _make_document("   \n\n  ")
        chunks = chunk_document(doc, chunk_size=512)
        assert chunks == []

    def test_long_text_multiple_chunks(self):
        text = "word " * 200  # 1000 chars
        doc = _make_document(text)
        chunks = chunk_document(doc, chunk_size=100, chunk_overlap=20)
        assert len(chunks) > 1

        # All chunks should have content
        for chunk in chunks:
            assert len(chunk.content) > 0
            assert chunk.document_id == doc.id

        # Indices should be sequential
        for i, chunk in enumerate(chunks):
            assert chunk.index == i

    def test_chunks_have_metadata(self):
        doc = _make_document("Some content")
        chunks = chunk_document(doc, chunk_size=512)
        assert chunks[0].metadata["source_type"] == "test"
        assert chunks[0].metadata["title"] == "Test Document"

    def test_chunk_ids_are_deterministic(self):
        doc = _make_document("Deterministic content")
        chunks1 = chunk_document(doc, chunk_size=512)
        chunks2 = chunk_document(doc, chunk_size=512)
        assert chunks1[0].id == chunks2[0].id

    def test_overlap_produces_shared_content(self):
        text = "A" * 100 + "B" * 100
        doc = _make_document(text)
        chunks = chunk_document(doc, chunk_size=100, chunk_overlap=20)
        assert len(chunks) >= 2
