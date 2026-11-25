"""Logical disjunction AST node (left OR right)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeVar

from rql.ast.nodes.rql_node import RqlNode

if TYPE_CHECKING:
    from rql.ast.visitor import IRqlAstVisitor

TResult = TypeVar("TResult")


@dataclass(frozen=True)
class OrNode(RqlNode):
    """Composite node representing logical disjunction (left OR right)."""

    left: RqlNode
    right: RqlNode

    def accept(self, visitor: IRqlAstVisitor[TResult]) -> TResult:
        return visitor.visit_or(self)
