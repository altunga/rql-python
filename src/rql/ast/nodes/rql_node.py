"""Abstract base node in the RQL AST hierarchy."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from rql.ast.visitor import IRqlAstVisitor

TResult = TypeVar("TResult")


class RqlNode(ABC):
    """Abstract base component in the RQL AST hierarchy."""

    @abstractmethod
    def accept(self, visitor: IRqlAstVisitor[TResult]) -> TResult:
        """Accepts an AST visitor."""
