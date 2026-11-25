"""Protocol for RQL function resolvers."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, TypeVar, runtime_checkable

T_contra = TypeVar("T_contra", contravariant=True)


@runtime_checkable
class IRqlFunctionResolver(Protocol[T_contra]):
    """Resolves an RQL function call (e.g. '__fn:now()') to a concrete string value."""

    def handles(self, function_name: str) -> bool:
        """Returns True if this resolver supports the given function name."""
        ...

    def resolve(
        self,
        function_name: str,
        args: Sequence[str],
        context_entity: T_contra | None = None,
    ) -> str:
        """Evaluates the function and returns its resolved string representation."""
        ...
