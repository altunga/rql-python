"""Shared backend helpers for function value resolution and lookup/collection routing."""

from __future__ import annotations

import logging
from collections.abc import Iterable, Sequence
from typing import TypeVar

from rql.abstractions.functions import IRqlFunctionResolver
from rql.functions.builtin_resolver import FunctionResolverChain
from rql.strategies.operators import is_null_or_empty_token

T = TypeVar("T")

logger = logging.getLogger("rql")


def resolve_condition_values(
    raw_values: Sequence[str],
    function_resolvers: Iterable[IRqlFunctionResolver[T]],
) -> tuple[list[str], str, bool]:
    """Resolves function tokens in condition values and returns (resolved_values, first_value, is_null)."""
    chain = FunctionResolverChain(function_resolvers)
    resolved = [chain.resolve_token(v) for v in raw_values]
    first_value = resolved[0] if resolved else ""
    is_null = is_null_or_empty_token(first_value)
    return resolved, first_value, is_null
