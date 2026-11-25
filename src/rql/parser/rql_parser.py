"""Recursive-descent RQL parser building immutable RqlQuery ASTs (SRP)."""

from __future__ import annotations

from collections.abc import Sequence

from rql.ast.nodes import (
    AndNode,
    FieldConditionNode,
    NotNode,
    OrderByClause,
    OrNode,
    RqlNode,
    RqlQuery,
    SortField,
)
from rql.exceptions import RqlParseException
from rql.lexer.rql_lexer import RqlLexer
from rql.lexer.tokens import Token, TokenType

_OPERATOR_MAP: dict[TokenType, str] = {
    TokenType.EQUALS: "=",
    TokenType.NOT_EQUALS: "!=",
    TokenType.LESS_THAN: "<",
    TokenType.LESS_THAN_OR_EQUAL: "<=",
    TokenType.GREATER_THAN: ">",
    TokenType.GREATER_THAN_OR_EQUAL: ">=",
    TokenType.CONTAINS: "~",
    TokenType.NOT_CONTAINS: "!~",
    TokenType.IN: "in",
    TokenType.NOT_IN: "not in",
    TokenType.IS: "is",
    TokenType.IS_NOT: "is not",
    TokenType.WAS: "was",
    TokenType.WAS_IN: "was in",
    TokenType.WAS_NOT: "was not",
    TokenType.WAS_NOT_IN: "was not in",
    TokenType.CHANGED: "changed",
}

_LIST_OPERATORS: frozenset[str] = frozenset({"in", "not in", "was in", "was not in"})


class RqlParser:
    """Recursive-descent RQL parser.

    Grammar:
      query     = [ expr ] [ ORDER BY sort-list ] EOF
      expr      = term { OR term }
      term      = factor { AND factor }
      factor    = NOT factor | '(' expr ')' | condition
      condition = field operator value
    """

    def __init__(self, tokens: Sequence[Token]) -> None:
        self._tokens = list(tokens)
        self._pos = 0

    @staticmethod
    def parse(rql: str) -> RqlQuery:
        """Tokenizes and parses an RQL string into an RqlQuery AST."""
        tokens = RqlLexer(rql).tokenize()
        return RqlParser(tokens).parse_query()

    @property
    def _current(self) -> Token:
        return self._tokens[self._pos]

    def _consume(self) -> Token:
        tok = self._tokens[self._pos]
        if tok.type != TokenType.EOF:
            self._pos += 1
        return tok

    def _expect(self, expected_type: TokenType) -> Token:
        curr = self._current
        if curr.type != expected_type:
            raise RqlParseException(
                f"Expected {expected_type.name} but got '{curr.value}' at position {curr.position}"
            )
        return self._consume()

    def parse_query(self) -> RqlQuery:
        """Parses a full RQL query (optional WHERE + optional ORDER BY) and verifies EOF."""
        where: RqlNode | None = None
        if self._current.type not in (TokenType.EOF, TokenType.ORDER_BY):
            where = self._parse_expr()

        order_by: OrderByClause | None = None
        if self._current.type == TokenType.ORDER_BY:
            self._consume()  # ORDER
            self._expect(TokenType.BY)  # BY
            order_by = self._parse_order_by()

        if self._current.type != TokenType.EOF:
            curr = self._current
            raise RqlParseException(
                f"Unexpected token '{curr.value}' at position {curr.position}"
            )

        return RqlQuery(where=where, order_by=order_by)

    def _parse_expr(self) -> RqlNode:
        left = self._parse_term()
        while self._current.type == TokenType.OR:
            self._consume()
            left = OrNode(left=left, right=self._parse_term())
        return left

    def _parse_term(self) -> RqlNode:
        left = self._parse_factor()
        while self._current.type == TokenType.AND:
            self._consume()
            left = AndNode(left=left, right=self._parse_factor())
        return left

    def _parse_factor(self) -> RqlNode:
        if self._current.type == TokenType.NOT:
            self._consume()
            return NotNode(operand=self._parse_factor())
        if self._current.type == TokenType.LPAREN:
            self._consume()
            inner = self._parse_expr()
            self._expect(TokenType.RPAREN)
            return inner
        return self._parse_condition()

    def _parse_condition(self) -> RqlNode:
        field_tok = self._expect(TokenType.IDENTIFIER)
        op = self._parse_operator()
        values = self._parse_values(op)
        return FieldConditionNode(
            field=field_tok.value.lower(),
            operator=op,
            values=tuple(values),
        )

    def _parse_operator(self) -> str:
        curr = self._current
        op = _OPERATOR_MAP.get(curr.type)
        if op is None:
            raise RqlParseException(
                f"Expected operator but got '{curr.value}' at position {curr.position}"
            )
        self._consume()
        return op

    def _parse_values(self, op: str) -> list[str]:
        if op == "changed":
            return []

        if op in _LIST_OPERATORS:
            items: list[str] = []
            self._expect(TokenType.LPAREN)
            items.append(self._parse_single_value())
            while self._current.type == TokenType.COMMA:
                self._consume()
                items.append(self._parse_single_value())
            self._expect(TokenType.RPAREN)
            return items

        return [self._parse_single_value()]

    def _parse_single_value(self) -> str:
        curr = self._current
        if curr.type in (TokenType.STRING, TokenType.NUMBER):
            self._consume()
            return curr.value

        if curr.type == TokenType.IDENTIFIER:
            self._consume()
            name = curr.value
            if self._tokens[self._pos].type == TokenType.LPAREN:
                self._consume()  # (
                args: list[str] = []
                if self._tokens[self._pos].type != TokenType.RPAREN:
                    args.append(self._parse_single_value())
                    while self._tokens[self._pos].type == TokenType.COMMA:
                        self._consume()
                        args.append(self._parse_single_value())
                self._expect(TokenType.RPAREN)
                return f"__fn:{name}({','.join(args)})" if args else f"__fn:{name}()"
            return name

        raise RqlParseException(
            f"Expected value but got '{curr.value}' at position {curr.position}"
        )

    def _parse_order_by(self) -> OrderByClause:
        fields: list[SortField] = [self._parse_sort_field()]
        while self._current.type == TokenType.COMMA:
            self._consume()
            fields.append(self._parse_sort_field())
        return OrderByClause(fields=tuple(fields))

    def _parse_sort_field(self) -> SortField:
        field_name = self._expect(TokenType.IDENTIFIER).value.lower()
        asc = True
        if self._current.type == TokenType.ASC:
            self._consume()
            asc = True
        elif self._current.type == TokenType.DESC:
            self._consume()
            asc = False
        return SortField(field=field_name, asc=asc)
