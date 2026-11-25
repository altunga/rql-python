"""Unit tests for RqlLexer and Token definitions."""

from __future__ import annotations

import pytest

from rql.lexer.rql_lexer import RqlLexer
from rql.lexer.tokens import Token, TokenType


def test_tokenize_empty_string_returns_only_eof() -> None:
    tokens = RqlLexer("").tokenize()
    assert tokens == [Token(TokenType.EOF, "", 0)]


def test_tokenize_basic_comparison_operators() -> None:
    query = "= != < <= > >= ~ !~ ( ) ,"
    tokens = RqlLexer(query).tokenize()
    types = [t.type for t in tokens[:-1]]
    assert types == [
        TokenType.EQUALS,
        TokenType.NOT_EQUALS,
        TokenType.LESS_THAN,
        TokenType.LESS_THAN_OR_EQUAL,
        TokenType.GREATER_THAN,
        TokenType.GREATER_THAN_OR_EQUAL,
        TokenType.CONTAINS,
        TokenType.NOT_CONTAINS,
        TokenType.LPAREN,
        TokenType.RPAREN,
        TokenType.COMMA,
    ]


def test_tokenize_strings_and_escaped_quotes() -> None:
    query = '"hello \\"world\\"" \'single \\\'quote\\\'\''
    tokens = RqlLexer(query).tokenize()
    assert tokens[0] == Token(TokenType.STRING, 'hello "world"', 0)
    assert tokens[1].type == TokenType.STRING
    assert tokens[1].value == "single 'quote'"


def test_tokenize_numbers_including_negative_and_decimals() -> None:
    query = "42 -12.5 0.75"
    tokens = RqlLexer(query).tokenize()
    assert [t.value for t in tokens[:-1]] == ["42", "-12.5", "0.75"]
    assert all(t.type == TokenType.NUMBER for t in tokens[:-1])


def test_tokenize_single_and_compound_keywords() -> None:
    query = "AND OR NOT ( IN ) NOT IN IS IS NOT WAS ( ) WAS IN WAS NOT WAS NOT IN NOT WAS NOT WAS IN CHANGED ORDER BY ASC DESC"
    tokens = RqlLexer(query).tokenize()
    types = [t.type for t in tokens[:-1]]
    assert types == [
        TokenType.AND,
        TokenType.OR,
        TokenType.NOT,
        TokenType.LPAREN,
        TokenType.IN,
        TokenType.RPAREN,
        TokenType.NOT_IN,
        TokenType.IS,
        TokenType.IS_NOT,
        TokenType.WAS,
        TokenType.LPAREN,
        TokenType.RPAREN,
        TokenType.WAS_IN,
        TokenType.WAS_NOT,
        TokenType.WAS_NOT_IN,
        TokenType.WAS_NOT,
        TokenType.WAS_NOT_IN,
        TokenType.CHANGED,
        TokenType.ORDER_BY,
        TokenType.BY,
        TokenType.ASC,
        TokenType.DESC,
    ]


@pytest.mark.parametrize(
    ("query", "expected_first_type", "expected_first_value"),
    [
        ('notable = "yes"', TokenType.IDENTIFIER, "notable"),
        ('island = "crete"', TokenType.IDENTIFIER, "island"),
        ('washing = "done"', TokenType.IDENTIFIER, "washing"),
        ('NOT (status = "Closed")', TokenType.NOT, "NOT"),
        ("is_active = 1", TokenType.IDENTIFIER, "is_active"),
        ("custom-field = 2", TokenType.IDENTIFIER, "custom-field"),
    ],
)
def test_tokenize_keyword_prefixes_and_compound_rollback(
    query: str,
    expected_first_type: TokenType,
    expected_first_value: str,
) -> None:
    tokens = RqlLexer(query).tokenize()
    assert tokens[0].type == expected_first_type
    assert tokens[0].value == expected_first_value


def test_tokenize_skips_unknown_characters() -> None:
    tokens = RqlLexer("status @ = # 'Open'").tokenize()
    assert [(t.type, t.value) for t in tokens[:-1]] == [
        (TokenType.IDENTIFIER, "status"),
        (TokenType.EQUALS, "="),
        (TokenType.STRING, "Open"),
    ]
