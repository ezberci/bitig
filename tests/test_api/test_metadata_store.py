from datetime import datetime

import pytest

from src.models.chat import ChatHistoryItem, Source
from src.models.connector import ConnectorType, SyncStatus
from src.models.entity import Entity, EntityType, Relation, RelationType
from src.store.metadata import MetadataStore


class TestSyncState:
    async def test_get_default_connector_state(self, metadata_store: MetadataStore):
        state = await metadata_store.get_connector_state(ConnectorType.GMAIL)
        assert state.connector_type == ConnectorType.GMAIL
        assert state.configured is False
        assert state.status == SyncStatus.IDLE

    async def test_update_sync_state(self, metadata_store: MetadataStore):
        await metadata_store.update_sync_state(
            ConnectorType.GMAIL,
            status=SyncStatus.SUCCESS,
            document_count=42,
        )
        state = await metadata_store.get_connector_state(ConnectorType.GMAIL)
        assert state.configured is True
        assert state.status == SyncStatus.SUCCESS
        assert state.document_count == 42
        assert state.last_sync_at is not None

    async def test_update_sync_state_error(self, metadata_store: MetadataStore):
        await metadata_store.update_sync_state(
            ConnectorType.JIRA,
            status=SyncStatus.FAILED,
            error="Connection timeout",
        )
        state = await metadata_store.get_connector_state(ConnectorType.JIRA)
        assert state.status == SyncStatus.FAILED
        assert state.error == "Connection timeout"

    async def test_get_all_connector_states(self, metadata_store: MetadataStore):
        states = await metadata_store.get_all_connector_states()
        assert len(states) == len(ConnectorType)


class TestDocuments:
    async def test_upsert_document(self, metadata_store: MetadataStore):
        await metadata_store.upsert_document(
            doc_id="doc-1",
            source_type="gmail",
            source_id="msg-123",
            title="Test Email",
            timestamp=datetime(2025, 1, 15),
        )
        stats = await metadata_store.get_ingestion_stats()
        assert stats.total_documents == 1

    async def test_upsert_document_idempotent(self, metadata_store: MetadataStore):
        for _ in range(3):
            await metadata_store.upsert_document(
                doc_id="doc-1",
                source_type="gmail",
                source_id="msg-123",
                title="Test Email",
                timestamp=datetime(2025, 1, 15),
            )
        stats = await metadata_store.get_ingestion_stats()
        assert stats.total_documents == 1


class TestEntities:
    @pytest.fixture
    async def sample_entities(self, metadata_store: MetadataStore):
        entities = [
            Entity(
                id="ent-1",
                name="Arif",
                type=EntityType.PERSON,
                first_seen=datetime(2025, 1, 1),
                last_seen=datetime(2025, 1, 15),
            ),
            Entity(
                id="ent-2",
                name="AUTH-123",
                type=EntityType.TICKET,
                first_seen=datetime(2025, 1, 5),
                last_seen=datetime(2025, 1, 10),
            ),
            Entity(
                id="ent-3",
                name="Database Migration",
                type=EntityType.TOPIC,
                first_seen=datetime(2025, 1, 3),
                last_seen=datetime(2025, 1, 12),
            ),
        ]
        for e in entities:
            await metadata_store.upsert_entity(e)
        return entities

    async def test_upsert_and_get_entity(self, metadata_store: MetadataStore, sample_entities):
        entity = await metadata_store.get_entity("ent-1")
        assert entity.name == "Arif"
        assert entity.type == EntityType.PERSON

    async def test_get_entity_not_found(self, metadata_store: MetadataStore):
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await metadata_store.get_entity("nonexistent")
        assert exc_info.value.status_code == 404

    async def test_list_entities(self, metadata_store: MetadataStore, sample_entities):
        entities = await metadata_store.get_entities()
        assert len(entities) == 3

    async def test_filter_entities_by_type(self, metadata_store: MetadataStore, sample_entities):
        entities = await metadata_store.get_entities(entity_type=EntityType.PERSON)
        assert len(entities) == 1
        assert entities[0].name == "Arif"

    async def test_search_entities_by_name(self, metadata_store: MetadataStore, sample_entities):
        entities = await metadata_store.get_entities(query="AUTH")
        assert len(entities) == 1
        assert entities[0].name == "AUTH-123"

    async def test_entity_upsert_updates_last_seen(self, metadata_store: MetadataStore):
        entity = Entity(
            id="ent-1",
            name="Arif",
            type=EntityType.PERSON,
            first_seen=datetime(2025, 1, 1),
            last_seen=datetime(2025, 1, 15),
        )
        await metadata_store.upsert_entity(entity)

        updated = Entity(
            id="ent-1",
            name="Arif Ezberci",
            type=EntityType.PERSON,
            first_seen=datetime(2025, 1, 1),
            last_seen=datetime(2025, 2, 1),
        )
        await metadata_store.upsert_entity(updated)

        result = await metadata_store.get_entity("ent-1")
        assert result.name == "Arif Ezberci"
        assert result.last_seen == datetime(2025, 2, 1)


class TestRelations:
    async def test_add_relation_and_graph(self, metadata_store: MetadataStore):
        # Create entities
        pairs = [("e1", "Arif", EntityType.PERSON), ("e2", "AUTH-123", EntityType.TICKET)]
        for eid, name, etype in pairs:
            await metadata_store.upsert_entity(
                Entity(
                    id=eid,
                    name=name,
                    type=etype,
                    first_seen=datetime(2025, 1, 1),
                    last_seen=datetime(2025, 1, 15),
                )
            )

        # Create document
        await metadata_store.upsert_document(
            doc_id="doc-1",
            source_type="gmail",
            source_id="msg-1",
            title="Email",
            timestamp=datetime(2025, 1, 15),
        )

        # Add relation
        rel = Relation(
            entity_a_id="e1",
            entity_b_id="e2",
            relation_type=RelationType.MENTIONED_IN,
            document_id="doc-1",
        )
        await metadata_store.add_relation(rel)

        # Check graph
        graph = await metadata_store.get_entity_graph()
        assert len(graph.nodes) == 2
        assert len(graph.edges) == 1
        assert graph.edges[0].relation_type == RelationType.MENTIONED_IN


class TestChatHistory:
    async def test_save_and_get_chat_history(self, metadata_store: MetadataStore):
        item = ChatHistoryItem(
            id="chat-1",
            question="What happened today?",
            answer="Several meetings were held.",
            sources=[
                Source(
                    document_id="doc-1",
                    title="Meeting Notes",
                    source_type="meet",
                    snippet="We discussed...",
                    timestamp=datetime(2025, 1, 15),
                )
            ],
            created_at=datetime(2025, 1, 15, 14, 30),
        )
        await metadata_store.save_chat(item)

        history = await metadata_store.get_chat_history(limit=10)
        assert len(history) == 1
        assert history[0].question == "What happened today?"
        assert len(history[0].sources) == 1
        assert history[0].sources[0].title == "Meeting Notes"

    async def test_chat_history_ordering(self, metadata_store: MetadataStore):
        for i in range(5):
            await metadata_store.save_chat(
                ChatHistoryItem(
                    id=f"chat-{i}",
                    question=f"Question {i}",
                    answer=f"Answer {i}",
                    created_at=datetime(2025, 1, 15, 10 + i),
                )
            )

        history = await metadata_store.get_chat_history(limit=3)
        assert len(history) == 3
        assert history[0].question == "Question 4"  # most recent first

    async def test_empty_chat_history(self, metadata_store: MetadataStore):
        history = await metadata_store.get_chat_history()
        assert history == []


class TestIngestionStats:
    async def test_empty_stats(self, metadata_store: MetadataStore):
        stats = await metadata_store.get_ingestion_stats()
        assert stats.total_documents == 0
        assert stats.total_entities == 0
        assert stats.total_relations == 0

    async def test_stats_after_inserts(self, metadata_store: MetadataStore):
        await metadata_store.upsert_document(
            doc_id="d1",
            source_type="gmail",
            source_id="m1",
            title="Email",
            timestamp=datetime(2025, 1, 15),
        )
        await metadata_store.upsert_entity(
            Entity(
                id="e1",
                name="Arif",
                type=EntityType.PERSON,
                first_seen=datetime(2025, 1, 1),
                last_seen=datetime(2025, 1, 15),
            )
        )
        stats = await metadata_store.get_ingestion_stats()
        assert stats.total_documents == 1
        assert stats.total_entities == 1
