"""ORDER BY clause AST representation."""

from __future__ import annotations

from dataclasses import dataclass

from rql.ast.nodes.sort_field import SortField


@dataclass(frozen=True)
class OrderByClause:
    """Represents the ORDER BY clause of an RQL query."""

    fields: tuple[SortField, ...]

    def __init__(self, fields: tuple[SortField, ...] | list[SortField]) -> None:
        object.__setattr__(self, "fields", tuple(fields))
