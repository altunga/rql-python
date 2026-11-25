"""RQL Autocomplete Service providing field and value suggestions (SRP)."""

from __future__ import annotations

from rql.abstractions.services import IRqlAutocompleteService
from rql.metadata.schema import RqlMetadata
from rql.models.dtos import RqlAutocompleteResponse


class RqlAutocompleteService(IRqlAutocompleteService):
    """Returns autocomplete suggestions for an RQL field name or field value."""

    def __init__(self, meta: RqlMetadata) -> None:
        self._meta = meta

    def get_suggestions(self, field: str | None, query: str | None) -> RqlAutocompleteResponse:
        prefix = (query or "").strip()
        suggestions = (
            self._get_field_suggestions(prefix)
            if not field
            else self._get_value_suggestions(field, prefix)
        )
        return RqlAutocompleteResponse(suggestions=suggestions)

    def _get_field_suggestions(self, prefix: str) -> list[str]:
        prefix_lower = prefix.lower()
        candidates = [f.name for f in self._meta.fields] + [
            f"{fn.name}()" for fn in self._meta.functions
        ]
        return [c for c in candidates if c.lower().startswith(prefix_lower)][:20]

    def _get_value_suggestions(self, field: str, prefix: str) -> list[str]:
        f = self._meta.get_field(field.lower())
        if f is None:
            return []

        prefix_lower = prefix.lower()
        if f.allowed_values:
            return [v for v in f.allowed_values if prefix_lower in v.lower()][:20]

        if f.type == "date":
            date_fns = [
                f"{fn.name}()"
                for fn in self._meta.functions
                if fn.return_type == "date"
            ]
            return [fn for fn in date_fns if fn.lower().startswith(prefix_lower)][:20]

        return []
