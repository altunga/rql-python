"""Protocol for validating RQL syntax."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from rql.models.rql_validation_result import RqlValidationResult


@runtime_checkable
class IRqlValidationService(Protocol):
    """Validates RQL syntax and returns normalized output or error messages."""

    def validate(self, rql: str | None) -> RqlValidationResult:
        """Validates an RQL query string."""
        ...
