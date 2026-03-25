import structlog

from src.llm.base import BaseLLM

logger = structlog.get_logger()

RAG_SYSTEM_PROMPT = """\
You are Bitig, a personal work memory assistant. Answer the user's question \
based ONLY on the provided context. If the context doesn't contain enough \
information to answer, say so honestly. Always cite which sources you used.

Keep answers concise and actionable."""

RAG_USER_PROMPT = """\
Context:
{context}

Question: {question}

Answer the question based on the context above. If you reference specific \
information, mention which source it came from."""


class Generator:
    """Generates answers from retrieved context using an LLM."""

    def __init__(self, llm: BaseLLM) -> None:
        self._llm = llm

    async def generate(self, question: str, context_chunks: list[dict]) -> str:
        """Generate an answer from context chunks.

        Args:
            question: The user's question.
            context_chunks: Retrieved chunks with content and metadata.

        Returns:
            Generated answer string.
        """
        if not context_chunks:
            return "I couldn't find any relevant information to answer your question."

        context = self._format_context(context_chunks)
        prompt = RAG_USER_PROMPT.format(context=context, question=question)

        answer = await self._llm.generate(prompt, system=RAG_SYSTEM_PROMPT)
        logger.info("generator_response", question=question[:50], answer_len=len(answer))
        return answer

    def _format_context(self, chunks: list[dict]) -> str:
        """Format chunks into a context string for the LLM."""
        parts: list[str] = []
        for i, chunk in enumerate(chunks, 1):
            metadata = chunk.get("metadata", {})
            source = metadata.get("source_type", "unknown")
            title = metadata.get("title", "Untitled")
            content = chunk.get("content", "")
            parts.append(f"[Source {i}: {source}/{title}]\n{content}")
        return "\n\n".join(parts)
