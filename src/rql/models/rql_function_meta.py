"""Schema metadata DTO for a single RQL function."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RqlFunctionMeta:
    """Schema metadata for a single RQL function."""

    name: str
    return_type: str
    description: str
