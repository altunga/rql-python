"""GoF Visitor interface for RQL AST traversal (OCP & SRP)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, TypeVar

if TYPE_CHECKING:
    from rql.ast.nodes import AndNode, FieldConditionNode, NotNode, OrNode

TResult_co = TypeVar("TResult_co", covariant=True)


class IRqlAstVisitor(Protocol[TResult_co]):
    """Visitor protocol allowing new operations over the RQL AST without modifying node classes."""

    def visit_and(self, node: AndNode) -> TResult_co:
        """Visits a logical AND node."""
        ...

    def visit_or(self, node: OrNode) -> TResult_co:
        """Visits a logical OR node."""
        ...

    def visit_not(self, node: NotNode) -> TResult_co:
        """Visits a logical NOT node."""
        ...

    def visit_field_condition(self, node: FieldConditionNode) -> TResult_co:
        """Visits a leaf field condition node."""
        ...
