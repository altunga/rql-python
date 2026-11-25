"""Logical negation AST node (NOT operand)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeVar

from rql.ast.nodes.rql_node import RqlNode

if TYPE_CHECKING:
    from rql.ast.visitor import IRqlAstVisitor

TResult = TypeVar("TResult")


@dataclass(frozen=True)
class NotNode(RqlNode):
    """Composite unary node representing logical negation (NOT operand)."""

    operand: RqlNode

    def accept(self, visitor: IRqlAstVisitor[TResult]) -> TResult:
        return visitor.visit_not(self)
