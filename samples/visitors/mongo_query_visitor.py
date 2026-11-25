"""Sample custom AST Visitor translating an RqlQuery AST into a MongoDB filter dict."""

from __future__ import annotations

from typing import Any

from rql.ast.nodes import AndNode, FieldConditionNode, NotNode, OrNode
from rql.ast.visitor import IRqlAstVisitor


class MongoQueryVisitor(IRqlAstVisitor[dict[str, Any]]):
    """Demonstrates extending RQL with a custom target query compiler."""

    def visit_and(self, node: AndNode) -> dict[str, Any]:
        return {"$and": [node.left.accept(self), node.right.accept(self)]}

    def visit_or(self, node: OrNode) -> dict[str, Any]:
        return {"$or": [node.left.accept(self), node.right.accept(self)]}

    def visit_not(self, node: NotNode) -> dict[str, Any]:
        return {"$nor": [node.operand.accept(self)]}

    def visit_field_condition(self, node: FieldConditionNode) -> dict[str, Any]:
        op = node.operator
        first = node.values[0] if node.values else ""
        if op == "=":
            return {node.field: first}
        if op == "!=":
            return {node.field: {"$ne": first}}
        if op in ("in", "was in"):
            return {node.field: {"$in": list(node.values)}}
        if op in ("not in", "was not in"):
            return {node.field: {"$nin": list(node.values)}}
        if op == "~":
            return {node.field: {"$regex": first, "$options": "i"}}
        return {node.field: {"$exists": True}}
