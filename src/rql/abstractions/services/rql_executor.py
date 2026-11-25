"""Protocol for generic RQL AST query executors."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, TypeVar, runtime_checkable

if TYPE_CHECKING:
    from rql.ast.nodes import RqlQuery

T_co = TypeVar("T_co", covariant=True)
TQuery = TypeVar("TQuery")


@runtime_checkable
class IRqlExecutor(Protocol[T_co, TQuery]):
    """Generic RQL AST evaluator applying WHERE and ORDER BY to a query source."""

    def execute(self, source: TQuery, query: RqlQuery) -> TQuery:
        """Applies RQL filtering and ordering to source."""
        ...
