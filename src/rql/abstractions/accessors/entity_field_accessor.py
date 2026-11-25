"""Protocol for resolving a named field value or expression from an entity."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol, TypeVar, runtime_checkable

T_contra = TypeVar("T_contra", contravariant=True)


@runtime_checkable
class IEntityFieldAccessor(Protocol[T_contra]):
    """Resolves a named field value or query expression from an entity of type T."""

    def handles(self, field_name: str) -> bool:
        """Returns True if this accessor handles the given field name."""
        ...

    def get_value(self, entity: T_contra, field_name: str) -> Any:
        """Gets the runtime value of the field from the entity."""
        ...

    def get_expression(self, field_name: str) -> Callable[[T_contra], Any] | Any:
        """Returns a callable or ORM column expression for the given field."""
        ...
