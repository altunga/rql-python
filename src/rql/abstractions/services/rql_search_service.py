"""Protocol for paginated RQL search services."""

from __future__ import annotations

from typing import Protocol, TypeVar, runtime_checkable

from rql.models.paged_result import PagedResult

T_co = TypeVar("T_co", covariant=True)
TModel = TypeVar("TModel")


@runtime_checkable
class IRqlSearchService(Protocol[T_co, TModel]):
    """Executes an RQL string against entities of type T and returns a PagedResult of TModel."""

    def search(self, rql: str | None, skip: int = 0, take: int = 50) -> PagedResult[TModel]:
        """Executes paged RQL search."""
        ...
