from fastapi import APIRouter, Depends

from src.dependencies import get_metadata_store
from src.models.chat import ChatHistoryItem, ChatRequest, ChatResponse
from src.store.metadata import MetadataStore

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Ask a question using RAG pipeline."""
    # TODO: Implement RAG pipeline in Phase 3
    return ChatResponse(
        answer="RAG pipeline not yet implemented.",
        sources=[],
    )


@router.get("/chat/history", response_model=list[ChatHistoryItem])
async def chat_history(
    limit: int = 20,
    metadata_store: MetadataStore = Depends(get_metadata_store),
) -> list[ChatHistoryItem]:
    """Get recent chat history."""
    return await metadata_store.get_chat_history(limit=limit)
