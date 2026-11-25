"""Leaf AST node representing a field predicate."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeVar

from rql.ast.nodes.rql_node import RqlNode

if TYPE_CHECKING:
    from rql.ast.visitor import IRqlAstVisitor

TResult = TypeVar("TResult")


@dataclass(frozen=True)
class FieldConditionNode(RqlNode):
    """Leaf node representing a field predicate (e.g. status = 'Open')."""

    field: str
    operator: str
    values: tuple[str, ...]

    def __init__(self, field: str, operator: str, values: tuple[str, ...] | list[str]) -> None:
        object.__setattr__(self, "field", field)
        object.__setattr__(self, "operator", operator)
        object.__setattr__(self, "values", tuple(values))

    def accept(self, visitor: IRqlAstVisitor[TResult]) -> TResult:
        return visitor.visit_field_condition(self)
