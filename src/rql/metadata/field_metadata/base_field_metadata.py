"""Abstract base class for entity field metadata."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FieldMetadata(ABC):
    """Abstract base strategy encapsulating field type, runtime access, and query expression access."""

    name: str
    field_type: type[Any]

    @abstractmethod
    def get_value(self, entity: Any) -> Any:
        """Gets the runtime value from the entity."""

    @abstractmethod
    def get_expression(self) -> Any:
        """Gets a callable or ORM expression for query translation."""

    def normalize_alias(self, alias: str) -> str:
        """Normalizes field name aliases to the canonical name."""
        return self.name
