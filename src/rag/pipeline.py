import uuid
from datetime import datetime

import structlog

from src.models.chat import ChatHistoryItem, ChatResponse, Source
from src.rag.generator import Generator
from src.rag.retriever import Retriever
from src.store.metadata import MetadataStore

logger = structlog.get_logger()


class RAGPipeline:
    """Orchestrates retrieval-augmented generation: query → retrieve → generate."""

    def __init__(
        self,
        retriever: Retriever,
        generator: Generator,
        metadata_store: MetadataStore,
    ) -> None:
        self._retriever = retriever
        self._generator = generator
        self._metadata = metadata_store

    async def ask(
        self,
        question: str,
        top_k: int = 5,
        source_filter: str | None = None,
    ) -> ChatResponse:
        """Answer a question using RAG.

        Args:
            question: The user's question.
            top_k: Number of chunks to retrieve.
            source_filter: Optional source type filter.

        Returns:
            ChatResponse with answer and sources.
        """
        chunks = await self._retriever.retrieve(
            query=question,
            top_k=top_k,
            source_filter=source_filter,
        )

        answer = await self._generator.generate(question, chunks)

        sources = [
            Source(
                document_id=chunk.get("metadata", {}).get("document_id", ""),
                title=chunk.get("metadata", {}).get("title", "Untitled"),
                source_type=chunk.get("metadata", {}).get("source_type", "unknown"),
                snippet=chunk.get("content", "")[:200],
                timestamp=datetime.fromisoformat(
                    chunk.get("metadata", {}).get("timestamp", datetime.now().isoformat())
                ),
            )
            for chunk in chunks
        ]

        response = ChatResponse(answer=answer, sources=sources)

        # Save to history
        history_item = ChatHistoryItem(
            id=str(uuid.uuid4()),
            question=question,
            answer=answer,
            sources=sources,
            created_at=response.created_at,
        )
        await self._metadata.save_chat(history_item)

        logger.info("rag_completed", question=question[:50], sources=len(sources))
        return response
