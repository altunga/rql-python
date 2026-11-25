"""Metadata for foreign-key lookup entity fields."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from rql.metadata.field_metadata.base_field_metadata import FieldMetadata


@dataclass(frozen=True)
class LookupFieldMetadata(FieldMetadata):
    """Metadata for lookup fields storing both scalar display expression and FK ID expression."""

    value_getter: Callable[[Any], Any]
    expression_getter: Callable[[], Any]
    fk_expression_getter: Callable[[], Any]

    def get_value(self, entity: Any) -> Any:
        if entity is None:
            raise ValueError("entity must not be None")
        return self.value_getter(entity)

    def get_expression(self) -> Any:
        return self.expression_getter()

    def get_fk_expression(self) -> Any:
        """Returns the FK integer expression/callable."""
        return self.fk_expression_getter()
