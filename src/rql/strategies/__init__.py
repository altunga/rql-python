"""Operator comparison strategies (GoF Strategy pattern)."""

from rql.strategies.operators import (
    ScalarOperatorRegistry,
    evaluate_scalar_operator,
)

__all__ = ["ScalarOperatorRegistry", "evaluate_scalar_operator"]
