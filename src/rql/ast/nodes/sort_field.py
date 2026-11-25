"""Single sort specification within an ORDER BY clause."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SortField:
    """Single sort specification within an ORDER BY clause."""

    field: str
    asc: bool = True
