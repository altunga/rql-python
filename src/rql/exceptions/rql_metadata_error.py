"""Exception raised when field metadata configuration or lookup fails."""

from __future__ import annotations

from rql.exceptions.rql_error import RqlError


class RqlMetadataError(RqlError):
    """Raised when field metadata configuration or lookup fails."""
