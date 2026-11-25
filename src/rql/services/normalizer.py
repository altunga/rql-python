"""RQL AST Normalizer implementing IRqlNormalizer and GoF Visitor pattern (IRqlAstVisitor[str])."""

from __future__ import annotations

from rql.abstractions.services import IRqlNormalizer
from rql.ast.nodes import (
    AndNode,
    FieldConditionNode,
    NotNode,
    OrNode,
    RqlQuery,
)
from rql.ast.visitor import IRqlAstVisitor


class RqlNormalizer(IRqlNormalizer, IRqlAstVisitor[str]):
    """Serializes an RqlQuery AST back to a canonical RQL string using the Visitor pattern (SRP & OCP)."""

    def normalize(self, query: RqlQuery) -> str:
        parts: list[str] = []
        if query.where is not None:
            parts.append(query.where.accept(self))

        if query.order_by is not None:
            sort_items = ", ".join(
                f"{sf.field} {'ASC' if sf.asc else 'DESC'}" for sf in query.order_by.fields
            )
            parts.append(f"ORDER BY {sort_items}")

        return " ".join(parts).strip()

    def visit_and(self, node: AndNode) -> str:
        return f"({node.left.accept(self)} AND {node.right.accept(self)})"

    def visit_or(self, node: OrNode) -> str:
        return f"({node.left.accept(self)} OR {node.right.accept(self)})"

    def visit_not(self, node: NotNode) -> str:
        return f"NOT {node.operand.accept(self)}"

    def visit_field_condition(self, node: FieldConditionNode) -> str:
        op_upper = node.operator.upper()
        count = len(node.values)
        if count == 0:
            return f"{node.field} {op_upper}"
        if count == 1 and op_upper not in ("IN", "NOT IN", "WAS IN", "WAS NOT IN"):
            return f'{node.field} {op_upper} "{node.values[0]}"'
        quoted = ", ".join(f'"{v}"' for v in node.values)
        return f"{node.field} {op_upper} ({quoted})"
