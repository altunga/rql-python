"""Immutable lexical token model."""

from __future__ import annotations

from dataclasses import dataclass

from rql.lexer.tokens.token_type import TokenType


@dataclass(frozen=True)
class Token:
    """Immutable lexical token with type, raw string value, and 0-based character position."""

    type: TokenType
    value: str
    position: int
