"""Enumeration of all lexical token types in RQL."""

from __future__ import annotations

from enum import Enum, auto


class TokenType(Enum):
    """Enumeration of all lexical token types in RQL."""

    IDENTIFIER = auto()
    STRING = auto()
    NUMBER = auto()
    LPAREN = auto()
    RPAREN = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    EQUALS = auto()
    NOT_EQUALS = auto()
    LESS_THAN = auto()
    LESS_THAN_OR_EQUAL = auto()
    GREATER_THAN = auto()
    GREATER_THAN_OR_EQUAL = auto()
    IN = auto()
    NOT_IN = auto()
    IS = auto()
    IS_NOT = auto()
    CONTAINS = auto()
    NOT_CONTAINS = auto()
    WAS = auto()
    WAS_IN = auto()
    WAS_NOT_IN = auto()
    WAS_NOT = auto()
    CHANGED = auto()
    ORDER_BY = auto()
    ASC = auto()
    DESC = auto()
    COMMA = auto()
    BY = auto()
    EOF = auto()
