from datetime import datetime

from src.entity.resolver import resolve_entities
from src.models.entity import Entity, EntityType


def _make_entity(
    name: str,
    etype: EntityType = EntityType.PERSON,
    entity_id: str = "",
) -> Entity:
    return Entity(
        id=entity_id or name.lower().replace(" ", "-"),
        name=name,
        type=etype,
        first_seen=datetime(2024, 1, 1),
        last_seen=datetime(2024, 1, 15),
    )


class TestResolveEntities:
    def test_no_existing_keeps_all_new(self):
        new = [_make_entity("Alice"), _make_entity("Bob")]
        resolved = resolve_entities(new, existing_entities=[])
        assert len(resolved) == 2

    def test_exact_match_updates_existing(self):
        existing = [_make_entity("Alice", entity_id="alice-1")]
        new_entity = _make_entity("Alice", entity_id="alice-2")
        new_entity.last_seen = datetime(2024, 6, 1)

        resolved = resolve_entities([new_entity], existing)
        assert len(resolved) == 1
        assert resolved[0].id == "alice-1"  # keeps existing ID
        assert resolved[0].last_seen == datetime(2024, 6, 1)

    def test_fuzzy_match(self):
        existing = [_make_entity("Alice Smith", entity_id="alice")]
        new = [_make_entity("Alice Smth", entity_id="alice-typo")]

        resolved = resolve_entities(new, existing, threshold=80)
        assert len(resolved) == 1
        assert resolved[0].id == "alice"  # matched to existing

    def test_no_match_below_threshold(self):
        existing = [_make_entity("Alice", entity_id="alice")]
        new = [_make_entity("Bob", entity_id="bob")]

        resolved = resolve_entities(new, existing)
        assert len(resolved) == 1
        assert resolved[0].id == "bob"  # new entity, not matched

    def test_different_types_not_matched(self):
        existing = [_make_entity("Sprint", etype=EntityType.PROJECT, entity_id="proj")]
        new = [_make_entity("Sprint", etype=EntityType.TOPIC, entity_id="topic")]

        resolved = resolve_entities(new, existing)
        assert len(resolved) == 1
        assert resolved[0].id == "topic"  # not matched due to type diff

    def test_metadata_merged_on_match(self):
        existing = [_make_entity("Alice", entity_id="alice")]
        existing[0].metadata = {"email": "alice@test.com"}

        new = [_make_entity("Alice", entity_id="alice-2")]
        new[0].metadata = {"source": "llm"}

        resolved = resolve_entities(new, existing)
        assert resolved[0].metadata["email"] == "alice@test.com"
        assert resolved[0].metadata["source"] == "llm"
