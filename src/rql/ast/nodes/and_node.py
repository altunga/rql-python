"""Logical conjunction AST node (left AND right)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeVar

from rql.ast.nodes.rql_node import RqlNode

if TYPE_CHECKING:
    from rql.ast.visitor import IRqlAstVisitor

TResult = TypeVar("TResult")


@dataclass(frozen=True)
class AndNode(RqlNode):
    """Composite node representing logical conjunction (left AND right)."""

    left: RqlNode
    right: RqlNode

    def accept(self, visitor: IRqlAstVisitor[TResult]) -> TResult:
        return visitor.visit_and(self)
