"""Protocol for read-only RQL schema metadata services."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from rql.models.rql_metadata_response import RqlMetadataResponse


@runtime_checkable
class IRqlMetadataService(Protocol):
    """Provides read-only RQL schema metadata (fields, operators, functions, keywords)."""

    def get_metadata(self) -> RqlMetadataResponse:
        """Returns full RQL schema metadata."""
        ...
