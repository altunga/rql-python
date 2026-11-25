"""In-memory user reference entity for sample collection fields."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UserRef:
    """Represents a user assigned to or watching an issue."""

    user_id: int
    username: str
