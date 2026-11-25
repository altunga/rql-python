"""FieldMetadataRegistry implementing the Registry pattern for centralized field metadata access."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from typing import Generic, TypeVar

from rql.metadata.field_metadata import FieldMetadata

T = TypeVar("T")


class FieldMetadataRegistry(Generic[T]):
    """Stores and retrieves canonical field metadata and aliases (SRP & Registry Pattern)."""

    def __init__(
        self,
        fields: dict[str, FieldMetadata],
        aliases: dict[str, list[str]],
    ) -> None:
        self._fields = dict(fields)
        self._aliases = {k: list(v) for k, v in aliases.items()}

    def get_field(self, field_name: str) -> FieldMetadata | None:
        """Resolves a field name or alias to its canonical FieldMetadata."""
        lower = field_name.lower()
        if lower in self._fields:
            return self._fields[lower]

        for canonical, alias_list in self._aliases.items():
            if lower in alias_list:
                return self._fields[canonical]

        return None

    def get_field_names(self) -> Iterable[str]:
        """Returns all registered canonical field names."""
        return self._fields.keys()

    def get_all_fields(self) -> Iterator[tuple[str, FieldMetadata, Iterable[str]]]:
        """Yields (canonical_name, metadata, aliases) for all registered fields."""
        for canonical, metadata in self._fields.items():
            aliases = self._aliases.get(canonical, [])
            yield (canonical, metadata, aliases)
