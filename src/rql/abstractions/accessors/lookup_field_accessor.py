"""Protocol for accessing the integer FK property/expression of a lookup field."""

from __future__ import annotations

from typing import Any, Protocol, TypeVar, runtime_checkable

T_co = TypeVar("T_co", covariant=True)


@runtime_checkable
class ILookupFieldAccessor(Protocol[T_co]):
    """Provides access to the integer FK property/expression of a lookup field."""

    def is_lookup_field(self, field_name: str) -> bool:
        """Returns True if this accessor handles the given lookup field."""
        ...

    def get_fk_expression(self, field_name: str) -> Any:
        """Returns a callable (entity -> int) or ORM column expression accessing the FK property."""
        ...
