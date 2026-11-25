"""Protocol for RQL autocomplete suggestion services."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from rql.models.rql_autocomplete_response import RqlAutocompleteResponse


@runtime_checkable
class IRqlAutocompleteService(Protocol):
    """Returns autocomplete suggestions for an RQL field and prefix query."""

    def get_suggestions(self, field: str | None, query: str | None) -> RqlAutocompleteResponse:
        """Returns matching suggestions for field names or field values."""
        ...
