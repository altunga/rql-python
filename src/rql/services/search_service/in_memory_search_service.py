"""Paginated RQL search service over in-memory entities."""

from __future__ import annotations

import math
from collections.abc import Callable, Iterable
from typing import Any, Generic, TypeVar

from rql.abstractions.services import IRqlExecutor, IRqlSearchService
from rql.models.paged_result import PagedResult
from rql.parser.rql_parser import RqlParser

T = TypeVar("T")
TModel = TypeVar("TModel")


class InMemoryRqlSearchService(Generic[T, TModel], IRqlSearchService[T, TModel]):
    """Executes an RQL string against in-memory entities and returns a PagedResult."""

    def __init__(
        self,
        source_provider: Callable[[], Iterable[T]],
        executor: IRqlExecutor[T, Any],
        mapper: Callable[[T], TModel],
    ) -> None:
        self._source_provider = source_provider
        self._executor = executor
        self._mapper = mapper

    def search(self, rql: str | None, skip: int = 0, take: int = 50) -> PagedResult[TModel]:
        query = RqlParser.parse(rql or "")
        filtered = list(self._executor.execute(self._source_provider(), query))
        total = len(filtered)
        safe_skip = max(0, skip)
        safe_take = max(1, take)
        total_pages = math.ceil(total / safe_take) if total > 0 else 0
        page_slice = filtered[safe_skip : safe_skip + safe_take]

        return PagedResult(
            total=total,
            skip=safe_skip,
            take=safe_take,
            total_pages=total_pages,
            rql=rql,
            items=[self._mapper(item) for item in page_slice],
        )
