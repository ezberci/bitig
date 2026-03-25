from datetime import datetime

from src.models.chat import ChatRequest, ChatResponse, Source
from src.models.connector import ConnectorState, ConnectorType, IngestionStats, SyncStatus
from src.models.document import Chunk, Document, RawDocument
from src.models.entity import Entity, EntityGraph, EntityType, Relation, RelationType


class TestDocumentModels:
    def test_raw_document_creation(self):
        doc = RawDocument(
            source_type="gmail",
            source_id="msg-123",
            title="Test Email",
            content="Hello world",
            timestamp=datetime(2025, 1, 15),
        )
        assert doc.source_type == "gmail"
        assert doc.metadata == {}

    def test_raw_document_with_metadata(self):
        doc = RawDocument(
            source_type="jira",
            source_id="PROJ-123",
            title="Bug fix",
            content="Description",
            metadata={"assignee": "arif", "sprint": "Sprint 5"},
            timestamp=datetime(2025, 1, 15),
        )
        assert doc.metadata["assignee"] == "arif"

    def test_document_creation(self):
        doc = Document(
            id="doc-1",
            source_type="gmail",
            source_id="msg-123",
            title="Test",
            content="Content",
            timestamp=datetime(2025, 1, 15),
        )
        assert doc.id == "doc-1"

    def test_chunk_creation(self):
        chunk = Chunk(
            id="chunk-1",
            document_id="doc-1",
            content="Some text",
            index=0,
        )
        assert chunk.embedding is None
        assert chunk.metadata == {}

    def test_chunk_with_embedding(self):
        chunk = Chunk(
            id="chunk-1",
            document_id="doc-1",
            content="Some text",
            index=0,
            embedding=[0.1, 0.2, 0.3],
        )
        assert len(chunk.embedding) == 3


class TestEntityModels:
    def test_entity_creation(self):
        entity = Entity(
            id="ent-1",
            name="Arif",
            type=EntityType.PERSON,
            first_seen=datetime(2025, 1, 1),
            last_seen=datetime(2025, 1, 15),
        )
        assert entity.type == EntityType.PERSON

    def test_relation_creation(self):
        rel = Relation(
            entity_a_id="ent-1",
            entity_b_id="ent-2",
            relation_type=RelationType.MENTIONED_IN,
            document_id="doc-1",
        )
        assert rel.confidence == 1.0

    def test_entity_graph(self):
        entity = Entity(
            id="ent-1",
            name="Arif",
            type=EntityType.PERSON,
            first_seen=datetime(2025, 1, 1),
            last_seen=datetime(2025, 1, 15),
        )
        graph = EntityGraph(nodes=[entity], edges=[])
        assert len(graph.nodes) == 1
        assert len(graph.edges) == 0

    def test_entity_type_values(self):
        assert EntityType.PERSON == "person"
        assert EntityType.TICKET == "ticket"
        assert EntityType.DECISION == "decision"


class TestChatModels:
    def test_chat_request_defaults(self):
        req = ChatRequest(question="What happened?")
        assert req.top_k == 5
        assert req.source_filter is None

    def test_chat_response_with_sources(self):
        source = Source(
            document_id="doc-1",
            title="Meeting Notes",
            source_type="meet",
            snippet="We decided to...",
            timestamp=datetime(2025, 1, 15),
        )
        resp = ChatResponse(answer="The decision was...", sources=[source])
        assert len(resp.sources) == 1
        assert resp.created_at is not None


class TestConnectorModels:
    def test_connector_state_defaults(self):
        state = ConnectorState(connector_type=ConnectorType.GMAIL)
        assert state.configured is False
        assert state.status == SyncStatus.IDLE
        assert state.last_sync_at is None
        assert state.document_count == 0

    def test_ingestion_stats_defaults(self):
        stats = IngestionStats()
        assert stats.total_documents == 0
        assert stats.total_chunks == 0
        assert stats.total_entities == 0
