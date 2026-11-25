"""Metadata for simple scalar entity fields."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from rql.metadata.field_metadata.base_field_metadata import FieldMetadata


@dataclass(frozen=True)
class SimpleFieldMetadata(FieldMetadata):
    """Metadata for simple scalar fields (str, int, float, datetime, etc.)."""

    value_getter: Callable[[Any], Any]
    expression_getter: Callable[[], Any]

    def get_value(self, entity: Any) -> Any:
        if entity is None:
            raise ValueError("entity must not be None")
        return self.value_getter(entity)

    def get_expression(self) -> Any:
        return self.expression_getter()
