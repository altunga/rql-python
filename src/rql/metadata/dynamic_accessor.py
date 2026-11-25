"""DynamicEntityFieldAccessor implementing the GoF Adapter pattern over FieldMetadataRegistry."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from rql.abstractions.accessors import (
    ICollectionFieldAccessor,
    IEntityFieldAccessor,
    ILookupFieldAccessor,
)
from rql.metadata.field_metadata import (
    CollectionFieldMetadata,
    LookupFieldMetadata,
)
from rql.metadata.registry import FieldMetadataRegistry

T = TypeVar("T")


class DynamicEntityFieldAccessor(
    Generic[T],
    IEntityFieldAccessor[T],
    ILookupFieldAccessor[T],
    ICollectionFieldAccessor[T],
):
    """Generic dynamic field accessor adapting FieldMetadataRegistry[T] to RQL accessor protocols."""

    def __init__(self, metadata: FieldMetadataRegistry[T]) -> None:
        if metadata is None:
            raise ValueError("metadata must not be None")
        self._metadata = metadata

    # ── IEntityFieldAccessor[T] ──────────────────────────────────────────────

    def handles(self, field_name: str) -> bool:
        return self._metadata.get_field(field_name) is not None

    def get_value(self, entity: T, field_name: str) -> Any:
        metadata = self._metadata.get_field(field_name)
        if metadata is None:
            return None
        return metadata.get_value(entity)

    def get_expression(self, field_name: str) -> Any:
        metadata = self._metadata.get_field(field_name)
        if metadata is None:
            raise ValueError(f"Field '{field_name}' not found in metadata")
        return metadata.get_expression()

    # ── ILookupFieldAccessor[T] ──────────────────────────────────────────────

    def is_lookup_field(self, field_name: str) -> bool:
        metadata = self._metadata.get_field(field_name)
        return isinstance(metadata, LookupFieldMetadata)

    def get_fk_expression(self, field_name: str) -> Any:
        metadata = self._metadata.get_field(field_name)
        if not isinstance(metadata, LookupFieldMetadata):
            raise ValueError(f"Field '{field_name}' is not a lookup field")
        return metadata.get_fk_expression()

    # ── ICollectionFieldAccessor[T] ──────────────────────────────────────────

    def is_collection_field(self, field_name: str) -> bool:
        metadata = self._metadata.get_field(field_name)
        if metadata is None:
            return False
        return isinstance(metadata, CollectionFieldMetadata)

    def get_collection_contains_expression(self, field: str, value: str) -> Any:
        metadata = self._metadata.get_field(field)
        if not isinstance(metadata, CollectionFieldMetadata):
            raise ValueError(f"Field '{field}' is not a collection field")
        return metadata.get_collection_contains_expression(value)

    def get_collection_contains_substring_expression(self, field: str, value: str) -> Any:
        metadata = self._metadata.get_field(field)
        if not isinstance(metadata, CollectionFieldMetadata):
            raise ValueError(f"Field '{field}' is not a collection field")
        return metadata.get_collection_contains_substring_expression(value)

    def get_collection_is_empty_expression(self, field: str) -> Any:
        metadata = self._metadata.get_field(field)
        if not isinstance(metadata, CollectionFieldMetadata):
            raise ValueError(f"Field '{field}' is not a collection field")
        return metadata.get_collection_is_empty_expression()

    def get_collection_contains_by_id_expression(self, field: str, id_val: int) -> Any | None:
        metadata = self._metadata.get_field(field)
        if not isinstance(metadata, CollectionFieldMetadata):
            raise ValueError(f"Field '{field}' is not a collection field")
        return metadata.get_collection_contains_by_id_expression(id_val)

    def get_collection_contains_by_ids_expression(
        self, field: str, ids: list[int]
    ) -> Any | None:
        metadata = self._metadata.get_field(field)
        if not isinstance(metadata, CollectionFieldMetadata):
            raise ValueError(f"Field '{field}' is not a collection field")
        return metadata.get_collection_contains_by_ids_expression(ids)
