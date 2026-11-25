"""Exception raised when RQL syntax parsing or tokenization fails."""

from __future__ import annotations

from rql.exceptions.rql_error import RqlError


class RqlParseException(RqlError):
    """Raised when an RQL string cannot be tokenized or parsed into a valid AST."""
