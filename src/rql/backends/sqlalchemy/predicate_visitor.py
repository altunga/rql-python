"""AST Visitor compiling RqlNode trees into SQLAlchemy ColumnElement[bool] expressions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from sqlalchemy import and_, not_, or_
from sqlalchemy.sql import ColumnElement

from rql.ast.nodes import AndNode, FieldConditionNode, NotNode, OrNode
from rql.ast.visitor import IRqlAstVisitor

if TYPE_CHECKING:
    from rql.backends.sqlalchemy.executor import SqlAlchemyRqlExecutor

T = TypeVar("T")


class SqlAlchemyPredicateVisitor(Generic[T], IRqlAstVisitor[ColumnElement[bool]]):
    """AST Visitor compiling RqlNode trees into SQLAlchemy ColumnElement[bool] expressions."""

    def __init__(self, executor: SqlAlchemyRqlExecutor[T]) -> None:
        self._executor = executor

    def visit_and(self, node: AndNode) -> ColumnElement[bool]:
        return and_(node.left.accept(self), node.right.accept(self))

    def visit_or(self, node: OrNode) -> ColumnElement[bool]:
        return or_(node.left.accept(self), node.right.accept(self))

    def visit_not(self, node: NotNode) -> ColumnElement[bool]:
        return not_(node.operand.accept(self))

    def visit_field_condition(self, node: FieldConditionNode) -> ColumnElement[bool]:
        return self._executor._build_condition_expression(node)
