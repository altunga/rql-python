"""Paginated RQL search service over a SQLAlchemy 2.0 Session and Select statement."""

from __future__ import annotations

import math
from collections.abc import Callable, Iterable
from typing import Any, Generic, TypeVar

from rql.abstractions.services import IRqlExecutor, IRqlSearchService
from rql.models.paged_result import PagedResult
from rql.parser.rql_parser import RqlParser

T = TypeVar("T")
TModel = TypeVar("TModel")


class SqlAlchemyRqlSearchService(Generic[T, TModel], IRqlSearchService[T, TModel]):
    """Executes an RQL string against a SQLAlchemy 2.0 Session and base Select statement."""

    def __init__(
        self,
        session_factory: Callable[[], Any],
        base_select_provider: Callable[[], Any],
        executor: IRqlExecutor[T, Any],
        mapper: Callable[[T], TModel],
    ) -> None:
        self._session_factory = session_factory
        self._base_select_provider = base_select_provider
        self._executor = executor
        self._mapper = mapper

    def search(self, rql: str | None, skip: int = 0, take: int = 50) -> PagedResult[TModel]:
        from sqlalchemy import func, select

        query = RqlParser.parse(rql or "")
        stmt = self._executor.execute(self._base_select_provider(), query)
        safe_skip = max(0, skip)
        safe_take = max(1, take)

        session = self._session_factory()
        count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
        total: int = int(session.scalar(count_stmt) or 0)
        total_pages = math.ceil(total / safe_take) if total > 0 else 0

        paged_stmt = stmt.offset(safe_skip).limit(safe_take)
        rows: Iterable[T] = session.scalars(paged_stmt).all()

        return PagedResult(
            total=total,
            skip=safe_skip,
            take=safe_take,
            total_pages=total_pages,
            rql=rql,
            items=[self._mapper(row) for row in rows],
        )
