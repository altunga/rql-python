"""Result of validating an RQL string."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RqlValidationResult:
    """Result of validating an RQL string."""

    valid: bool = True
    errors: list[str] = field(default_factory=list)
    normalized_rql: str | None = None
