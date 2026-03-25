import structlog
from sentence_transformers import SentenceTransformer

from src.models.document import Chunk

logger = structlog.get_logger()


class Embedder:
    """Generates embeddings using sentence-transformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self._model_name = model_name
        self._model: SentenceTransformer | None = None

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            logger.info("loading_embedding_model", model=self._model_name)
            self._model = SentenceTransformer(self._model_name)
        return self._model

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors.
        """
        if not texts:
            return []
        embeddings = self.model.encode(texts, show_progress_bar=False)
        return [vec.tolist() for vec in embeddings]

    def embed_chunks(self, chunks: list[Chunk]) -> list[Chunk]:
        """Add embeddings to chunks in-place and return them.

        Args:
            chunks: List of chunks without embeddings.

        Returns:
            Same chunks with embeddings populated.
        """
        if not chunks:
            return chunks
        texts = [c.content for c in chunks]
        embeddings = self.embed_texts(texts)
        for chunk, embedding in zip(chunks, embeddings, strict=True):
            chunk.embedding = embedding
        return chunks

    def embed_query(self, query: str) -> list[float]:
        """Embed a single query string.

        Args:
            query: The query text.

        Returns:
            Embedding vector.
        """
        return self.model.encode(query, show_progress_bar=False).tolist()
