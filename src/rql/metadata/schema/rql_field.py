"""Schema definition for a single searchable RQL field."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RqlField:
    """Represents a single RQL searchable field in schema metadata."""

    name: str
    type: str
    allowed_values: list[str] = field(default_factory=list)
