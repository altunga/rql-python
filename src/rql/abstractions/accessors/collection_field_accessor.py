"""Protocol for many-to-many collection field accessors."""

from __future__ import annotations

from typing import Any, Protocol, TypeVar, runtime_checkable

T_co = TypeVar("T_co", covariant=True)


@runtime_checkable
class ICollectionFieldAccessor(Protocol[T_co]):
    """Extended accessor for many-to-many collection fields."""

    def is_collection_field(self, field_name: str) -> bool:
        """Returns True if this field name is backed by a collection."""
        ...

    def get_collection_contains_expression(self, field: str, value: str) -> Any:
        """Expression: any item in collection matches value (case-insensitive equality)."""
        ...

    def get_collection_contains_substring_expression(self, field: str, value: str) -> Any:
        """Expression: any item in collection contains value as substring."""
        ...

    def get_collection_is_empty_expression(self, field: str) -> Any:
        """Expression: collection has no elements."""
        ...

    def get_collection_contains_by_id_expression(self, field: str, id_val: int) -> Any | None:
        """Expression: any item in collection has FK ID == id_val, or None if unsupported."""
        ...

    def get_collection_contains_by_ids_expression(
        self, field: str, ids: list[int]
    ) -> Any | None:
        """Expression: any item in collection has FK ID in ids, or None if unsupported."""
        ...
