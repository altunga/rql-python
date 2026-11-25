"""Schema metadata DTO for a single RQL field."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RqlFieldMeta:
    """Schema metadata for a single RQL field."""

    name: str
    type: str
    allowed_values: list[str] = field(default_factory=list)
