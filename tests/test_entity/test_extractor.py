from unittest.mock import AsyncMock

from src.entity.extractor import (
    build_relations,
    extract_entities,
    extract_rule_based,
)
from src.models.entity import EntityType, RelationType


class TestRuleBasedExtraction:
    def test_extracts_emails(self):
        text = "Contact alice.smith@example.com for details"
        entities = extract_rule_based(text)
        assert len(entities) == 1
        assert entities[0].type == EntityType.PERSON
        assert entities[0].metadata["email"] == "alice.smith@example.com"
        assert entities[0].name == "Alice Smith"

    def test_extracts_tickets(self):
        text = "See PROJ-123 and DATA-4567 for context"
        entities = extract_rule_based(text)
        tickets = [e for e in entities if e.type == EntityType.TICKET]
        assert len(tickets) == 2
        names = {t.name for t in tickets}
        assert "PROJ-123" in names
        assert "DATA-4567" in names

    def test_extracts_both_emails_and_tickets(self):
        text = "bob@test.com filed PROJ-42"
        entities = extract_rule_based(text)
        types = {e.type for e in entities}
        assert EntityType.PERSON in types
        assert EntityType.TICKET in types

    def test_no_entities_in_plain_text(self):
        text = "Just a normal sentence without any entities"
        entities = extract_rule_based(text)
        assert entities == []

    def test_entity_ids_are_stable(self):
        text = "alice@example.com"
        e1 = extract_rule_based(text)
        e2 = extract_rule_based(text)
        assert e1[0].id == e2[0].id


class TestLLMExtraction:
    async def test_extract_with_llm(self):
        mock_llm = AsyncMock()
        mock_llm.generate_structured.return_value = {
            "entities": [
                {"name": "Alice", "type": "person"},
                {"name": "Bitig", "type": "project"},
            ]
        }

        entities = await extract_entities("Alice is working on Bitig", llm=mock_llm)
        names = {e.name for e in entities}
        assert "Alice" in names
        assert "Bitig" in names

    async def test_llm_failure_falls_back_to_rules(self):
        mock_llm = AsyncMock()
        mock_llm.generate_structured.side_effect = RuntimeError("LLM down")

        text = "bob@test.com mentioned PROJ-1"
        entities = await extract_entities(text, llm=mock_llm)
        # Should still get rule-based entities
        assert len(entities) >= 2

    async def test_llm_invalid_type_skipped(self):
        mock_llm = AsyncMock()
        mock_llm.generate_structured.return_value = {
            "entities": [
                {"name": "Valid", "type": "person"},
                {"name": "Invalid", "type": "unknown_type"},
            ]
        }

        entities = await extract_entities("test", llm=mock_llm)
        names = {e.name for e in entities}
        assert "Valid" in names
        assert "Invalid" not in names

    async def test_no_llm_only_rules(self):
        text = "alice@test.com"
        entities = await extract_entities(text, llm=None)
        assert len(entities) == 1
        assert entities[0].type == EntityType.PERSON


class TestBuildRelations:
    def test_builds_mentioned_in_relations(self):
        entities = extract_rule_based("alice@test.com and PROJ-1")
        relations = build_relations(entities, document_id="doc-1")
        assert len(relations) == len(entities)
        for r in relations:
            assert r.relation_type == RelationType.MENTIONED_IN
            assert r.document_id == "doc-1"

    def test_empty_entities_no_relations(self):
        relations = build_relations([], document_id="doc-1")
        assert relations == []
