import json
from datetime import datetime

import aiosqlite
import structlog

from src.config import settings
from src.models.chat import ChatHistoryItem, Source
from src.models.connector import ConnectorState, ConnectorType, IngestionStats, SyncStatus
from src.models.entity import Entity, EntityGraph, EntityType, Relation, RelationType

logger = structlog.get_logger()

SCHEMA = """
CREATE TABLE IF NOT EXISTS sync_state (
    connector_type TEXT PRIMARY KEY,
    status TEXT NOT NULL DEFAULT 'idle',
    last_sync_at TEXT,
    document_count INTEGER NOT NULL DEFAULT 0,
    error TEXT
);

CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    source_id TEXT NOT NULL,
    title TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    synced_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS entities (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    metadata TEXT NOT NULL DEFAULT '{}',
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_a_id TEXT NOT NULL,
    entity_b_id TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    document_id TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 1.0,
    FOREIGN KEY (entity_a_id) REFERENCES entities(id),
    FOREIGN KEY (entity_b_id) REFERENCES entities(id),
    FOREIGN KEY (document_id) REFERENCES documents(id)
);

CREATE TABLE IF NOT EXISTS chat_history (
    id TEXT PRIMARY KEY,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    sources TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type);
CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name);
CREATE INDEX IF NOT EXISTS idx_relations_entity_a ON relations(entity_a_id);
CREATE INDEX IF NOT EXISTS idx_relations_entity_b ON relations(entity_b_id);
CREATE INDEX IF NOT EXISTS idx_documents_source ON documents(source_type, source_id);
"""


class MetadataStore:
    """SQLite-based metadata storage for sync state, entities, and relations."""

    def __init__(self) -> None:
        self.db_path = settings.sqlite_path
        self._db: aiosqlite.Connection | None = None

    async def initialize(self) -> None:
        """Create database and tables."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db = await aiosqlite.connect(str(self.db_path))
        self._db.row_factory = aiosqlite.Row
        await self._db.executescript(SCHEMA)
        await self._db.commit()
        logger.info("metadata_store_initialized", path=str(self.db_path))

    async def close(self) -> None:
        if self._db:
            await self._db.close()

    @property
    def db(self) -> aiosqlite.Connection:
        assert self._db is not None, "MetadataStore not initialized"
        return self._db

    # --- Connector State ---

    async def get_all_connector_states(self) -> list[ConnectorState]:
        states = []
        for ct in ConnectorType:
            states.append(await self.get_connector_state(ct))
        return states

    async def get_connector_state(self, connector_type: ConnectorType) -> ConnectorState:
        async with self.db.execute(
            "SELECT * FROM sync_state WHERE connector_type = ?", (connector_type,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return ConnectorState(
                    connector_type=ConnectorType(row["connector_type"]),
                    configured=True,
                    status=SyncStatus(row["status"]),
                    last_sync_at=(
                        datetime.fromisoformat(row["last_sync_at"]) if row["last_sync_at"] else None
                    ),
                    document_count=row["document_count"],
                    error=row["error"],
                )
        return ConnectorState(connector_type=connector_type)

    async def update_sync_state(
        self,
        connector_type: ConnectorType,
        *,
        status: SyncStatus,
        document_count: int | None = None,
        error: str | None = None,
    ) -> None:
        now = datetime.now().isoformat()
        await self.db.execute(
            """INSERT INTO sync_state (connector_type, status, last_sync_at, document_count, error)
               VALUES (?, ?, ?, COALESCE(?, 0), ?)
               ON CONFLICT(connector_type) DO UPDATE SET
                 status = excluded.status,
                 last_sync_at = excluded.last_sync_at,
                 document_count = COALESCE(excluded.document_count, document_count),
                 error = excluded.error""",
            (connector_type, status, now, document_count, error),
        )
        await self.db.commit()

    # --- Documents ---

    async def upsert_document(
        self,
        doc_id: str,
        source_type: str,
        source_id: str,
        title: str,
        timestamp: datetime,
    ) -> None:
        now = datetime.now().isoformat()
        await self.db.execute(
            """INSERT INTO documents (id, source_type, source_id, title, timestamp, synced_at)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
                 title = excluded.title,
                 synced_at = excluded.synced_at""",
            (doc_id, source_type, source_id, title, timestamp.isoformat(), now),
        )
        await self.db.commit()

    # --- Entities ---

    async def get_entities(
        self,
        entity_type: EntityType | None = None,
        query: str | None = None,
        limit: int = 50,
    ) -> list[Entity]:
        sql = "SELECT * FROM entities WHERE 1=1"
        params: list[str | int] = []
        if entity_type:
            sql += " AND type = ?"
            params.append(entity_type)
        if query:
            sql += " AND name LIKE ?"
            params.append(f"%{query}%")
        sql += " ORDER BY last_seen DESC LIMIT ?"
        params.append(limit)

        async with self.db.execute(sql, params) as cursor:
            rows = await cursor.fetchall()
            return [
                Entity(
                    id=row["id"],
                    name=row["name"],
                    type=EntityType(row["type"]),
                    metadata=json.loads(row["metadata"]),
                    first_seen=datetime.fromisoformat(row["first_seen"]),
                    last_seen=datetime.fromisoformat(row["last_seen"]),
                )
                for row in rows
            ]

    async def get_entity(self, entity_id: str) -> Entity:
        async with self.db.execute("SELECT * FROM entities WHERE id = ?", (entity_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                from fastapi import HTTPException

                raise HTTPException(status_code=404, detail="Entity not found")
            return Entity(
                id=row["id"],
                name=row["name"],
                type=EntityType(row["type"]),
                metadata=json.loads(row["metadata"]),
                first_seen=datetime.fromisoformat(row["first_seen"]),
                last_seen=datetime.fromisoformat(row["last_seen"]),
            )

    async def get_entity_graph(self) -> EntityGraph:
        entities = await self.get_entities(limit=200)
        entity_ids = {e.id for e in entities}

        relations: list[Relation] = []
        async with self.db.execute(
            "SELECT * FROM relations WHERE entity_a_id IN ({}) OR entity_b_id IN ({})".format(
                ",".join("?" * len(entity_ids)),
                ",".join("?" * len(entity_ids)),
            ),
            [*entity_ids, *entity_ids],
        ) as cursor:
            rows = await cursor.fetchall()
            for row in rows:
                relations.append(
                    Relation(
                        entity_a_id=row["entity_a_id"],
                        entity_b_id=row["entity_b_id"],
                        relation_type=RelationType(row["relation_type"]),
                        document_id=row["document_id"],
                        confidence=row["confidence"],
                    )
                )

        return EntityGraph(nodes=entities, edges=relations)

    async def upsert_entity(self, entity: Entity) -> None:
        await self.db.execute(
            """INSERT INTO entities (id, name, type, metadata, first_seen, last_seen)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
                 name = excluded.name,
                 metadata = excluded.metadata,
                 last_seen = excluded.last_seen""",
            (
                entity.id,
                entity.name,
                entity.type,
                json.dumps(entity.metadata),
                entity.first_seen.isoformat(),
                entity.last_seen.isoformat(),
            ),
        )
        await self.db.commit()

    async def add_relation(self, relation: Relation) -> None:
        await self.db.execute(
            """INSERT INTO relations
               (entity_a_id, entity_b_id, relation_type, document_id, confidence)
               VALUES (?, ?, ?, ?, ?)""",
            (
                relation.entity_a_id,
                relation.entity_b_id,
                relation.relation_type,
                relation.document_id,
                relation.confidence,
            ),
        )
        await self.db.commit()

    # --- Chat History ---

    async def save_chat(self, item: ChatHistoryItem) -> None:
        await self.db.execute(
            """INSERT INTO chat_history
               (id, question, answer, sources, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (
                item.id,
                item.question,
                item.answer,
                json.dumps([s.model_dump(mode="json") for s in item.sources]),
                item.created_at.isoformat(),
            ),
        )
        await self.db.commit()

    async def get_chat_history(self, limit: int = 20) -> list[ChatHistoryItem]:
        async with self.db.execute(
            "SELECT * FROM chat_history ORDER BY created_at DESC LIMIT ?", (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [
                ChatHistoryItem(
                    id=row["id"],
                    question=row["question"],
                    answer=row["answer"],
                    sources=[Source(**s) for s in json.loads(row["sources"])],
                    created_at=datetime.fromisoformat(row["created_at"]),
                )
                for row in rows
            ]

    # --- Stats ---

    async def get_ingestion_stats(self) -> IngestionStats:
        doc_count = 0
        entity_count = 0
        relation_count = 0

        async with self.db.execute("SELECT COUNT(*) as c FROM documents") as cursor:
            row = await cursor.fetchone()
            if row:
                doc_count = row["c"]

        async with self.db.execute("SELECT COUNT(*) as c FROM entities") as cursor:
            row = await cursor.fetchone()
            if row:
                entity_count = row["c"]

        async with self.db.execute("SELECT COUNT(*) as c FROM relations") as cursor:
            row = await cursor.fetchone()
            if row:
                relation_count = row["c"]

        return IngestionStats(
            total_documents=doc_count,
            total_chunks=0,
            total_entities=entity_count,
            total_relations=relation_count,
        )
