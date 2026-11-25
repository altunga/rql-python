"""Schema definition for a single RQL function."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RqlFunction:
    """Represents a single RQL function in schema metadata."""

    name: str
    return_type: str
    description: str
