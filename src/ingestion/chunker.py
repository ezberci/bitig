import hashlib
import uuid

from src.models.document import Chunk, Document, RawDocument


def raw_to_document(raw: RawDocument) -> Document:
    """Convert a RawDocument to a Document with a stable ID."""
    doc_id = hashlib.sha256(f"{raw.source_type}:{raw.source_id}".encode()).hexdigest()[:16]
    return Document(
        id=doc_id,
        source_type=raw.source_type,
        source_id=raw.source_id,
        title=raw.title,
        content=raw.content,
        metadata=raw.metadata,
        timestamp=raw.timestamp,
    )


def chunk_document(
    document: Document,
    chunk_size: int = 512,
    chunk_overlap: int = 64,
) -> list[Chunk]:
    """Split a document into overlapping text chunks.

    Args:
        document: The document to chunk.
        chunk_size: Maximum characters per chunk.
        chunk_overlap: Number of overlapping characters between chunks.

    Returns:
        List of Chunk objects.
    """
    text = document.content.strip()
    if not text:
        return []

    chunks: list[Chunk] = []
    start = 0
    index = 0

    while start < len(text):
        end = start + chunk_size

        # Try to break at a sentence or paragraph boundary
        if end < len(text):
            for sep in ["\n\n", "\n", ". ", " "]:
                boundary = text.rfind(sep, start + chunk_size // 2, end)
                if boundary != -1:
                    end = boundary + len(sep)
                    break

        chunk_text = text[start:end].strip()
        if chunk_text:
            chunk_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{document.id}:{index}"))
            chunks.append(
                Chunk(
                    id=chunk_id,
                    document_id=document.id,
                    content=chunk_text,
                    index=index,
                    metadata={
                        "source_type": document.source_type,
                        "source_id": document.source_id,
                        "title": document.title,
                        "timestamp": document.timestamp.isoformat(),
                    },
                )
            )
            index += 1

        start = end - chunk_overlap if end < len(text) else end

    return chunks
