"""Root RQL query AST container."""

from __future__ import annotations

from dataclasses import dataclass

from rql.ast.nodes.order_by_clause import OrderByClause
from rql.ast.nodes.rql_node import RqlNode


@dataclass(frozen=True)
class RqlQuery:
    """Root AST container combining optional WHERE tree and ORDER BY clause."""

    where: RqlNode | None = None
    order_by: OrderByClause | None = None
