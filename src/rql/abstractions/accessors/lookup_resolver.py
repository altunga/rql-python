"""Protocol for resolving RQL display names to integer foreign-key IDs."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol, runtime_checkable


@runtime_checkable
class ILookupResolver(Protocol):
    """Resolves RQL display names (e.g. 'Open', 'Bug') to integer FK IDs."""

    def is_lookup_field(self, field_name: str) -> bool:
        """Returns True if the given field is a lookup field."""
        ...

    def resolve(self, field_name: str, display_value: str) -> int | None:
        """Resolves a display name to its integer ID, or None if not found."""
        ...

    def resolve_many(self, field_name: str, display_values: Iterable[str]) -> list[int]:
        """Resolves multiple display names to their integer IDs, skipping unknown values."""
        ...
