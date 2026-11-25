"""Autocomplete suggestions response model."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RqlAutocompleteResponse:
    """Autocomplete suggestions for an RQL field or value."""

    suggestions: list[str] = field(default_factory=list)
