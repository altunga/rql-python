"""Generic paged result wrapper returned by RQL search operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, TypeVar

TModel = TypeVar("TModel")


@dataclass
class PagedResult(Generic[TModel]):
    """Generic paged result wrapper returned by RQL search operations."""

    total: int = 0
    skip: int = 0
    take: int = 0
    total_pages: int = 0
    rql: str | None = None
    items: list[TModel] = field(default_factory=list)
