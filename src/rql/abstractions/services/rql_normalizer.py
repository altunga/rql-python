"""Protocol for serializing an RqlQuery AST to a canonical RQL string."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from rql.ast.nodes import RqlQuery


@runtime_checkable
class IRqlNormalizer(Protocol):
    """Serializes a parsed RqlQuery back to a canonical RQL string."""

    def normalize(self, query: RqlQuery) -> str:
        """Returns canonical RQL representation of query."""
        ...
