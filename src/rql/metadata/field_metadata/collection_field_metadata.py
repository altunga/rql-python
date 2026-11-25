"""Metadata for many-to-many collection entity fields."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from rql.metadata.field_metadata.base_field_metadata import FieldMetadata


@dataclass(frozen=True)
class CollectionFieldMetadata(FieldMetadata):
    """Metadata for many-to-many collection fields (reporter, assignee, etc.)."""

    value_getter: Callable[[Any], Any]
    expression_getter: Callable[[], Any]
    collection_contains_getter: Callable[[str], Any]
    collection_contains_substring_getter: Callable[[str], Any]
    collection_is_empty_getter: Callable[[], Any]
    collection_contains_by_id_getter: Callable[[int], Any] | None = None
    collection_contains_by_ids_getter: Callable[[list[int]], Any] | None = None

    def get_value(self, entity: Any) -> Any:
        if entity is None:
            raise ValueError("entity must not be None")
        return self.value_getter(entity)

    def get_expression(self) -> Any:
        return self.expression_getter()

    def get_collection_contains_expression(self, value: str) -> Any:
        return self.collection_contains_getter(value)

    def get_collection_contains_substring_expression(self, value: str) -> Any:
        return self.collection_contains_substring_getter(value)

    def get_collection_is_empty_expression(self) -> Any:
        return self.collection_is_empty_getter()

    def get_collection_contains_by_id_expression(self, id_val: int) -> Any | None:
        if self.collection_contains_by_id_getter is None:
            return None
        return self.collection_contains_by_id_getter(id_val)

    def get_collection_contains_by_ids_expression(self, ids: list[int]) -> Any | None:
        if self.collection_contains_by_ids_getter is None:
            return None
        return self.collection_contains_by_ids_getter(ids)
