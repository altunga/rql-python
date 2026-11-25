"""AST Visitor compiling RqlNode trees into in-memory predicate functions."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Generic, TypeVar

from rql.ast.nodes import AndNode, FieldConditionNode, NotNode, OrNode
from rql.ast.visitor import IRqlAstVisitor

if TYPE_CHECKING:
    from rql.backends.in_memory.executor import InMemoryRqlExecutor

T = TypeVar("T")
Predicate = Callable[[T], bool]


class InMemoryPredicateVisitor(Generic[T], IRqlAstVisitor[Predicate[T]]):
    """AST Visitor compiling RqlNode trees into in-memory predicate functions."""

    def __init__(self, executor: InMemoryRqlExecutor[T]) -> None:
        self._executor = executor

    def visit_and(self, node: AndNode) -> Predicate[T]:
        left = node.left.accept(self)
        right = node.right.accept(self)
        return lambda e: left(e) and right(e)

    def visit_or(self, node: OrNode) -> Predicate[T]:
        left = node.left.accept(self)
        right = node.right.accept(self)
        return lambda e: left(e) or right(e)

    def visit_not(self, node: NotNode) -> Predicate[T]:
        operand = node.operand.accept(self)
        return lambda e: not operand(e)

    def visit_field_condition(self, node: FieldConditionNode) -> Predicate[T]:
        return self._executor._build_condition_predicate(node)
