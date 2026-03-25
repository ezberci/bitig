from fastapi import APIRouter, Depends

from src.dependencies import get_metadata_store, get_rag_pipeline
from src.models.chat import ChatHistoryItem, ChatRequest, ChatResponse
from src.rag.pipeline import RAGPipeline
from src.store.metadata import MetadataStore

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    rag_pipeline: RAGPipeline = Depends(get_rag_pipeline),
) -> ChatResponse:
    """Ask a question using RAG pipeline."""
    return await rag_pipeline.ask(
        question=request.question,
        top_k=request.top_k,
        source_filter=request.source_filter,
    )


@router.get("/chat/history", response_model=list[ChatHistoryItem])
async def chat_history(
    limit: int = 20,
    metadata_store: MetadataStore = Depends(get_metadata_store),
) -> list[ChatHistoryItem]:
    """Get recent chat history."""
    return await metadata_store.get_chat_history(limit=limit)
