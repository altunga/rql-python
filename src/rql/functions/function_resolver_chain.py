"""Chain of Responsibility coordinator for RQL function resolvers."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Generic, TypeVar

from rql.abstractions.functions.rql_function_resolver import IRqlFunctionResolver

T = TypeVar("T")


class FunctionResolverChain(Generic[T]):
    """Dispatches function resolution requests across registered IRqlFunctionResolver instances."""

    def __init__(self, resolvers: Iterable[IRqlFunctionResolver[T]]) -> None:
        self._resolvers = list(resolvers)

    def resolve_token(self, value: str, context_entity: T | None = None) -> str:
        """Resolves '__fn:name(arg1,arg2)' tokens or returns regular values unchanged."""
        if not value.lower().startswith("__fn:"):
            return value

        fn_part = value[5:]
        paren_idx = fn_part.find("(")
        name = (fn_part[:paren_idx] if paren_idx >= 0 else fn_part).strip().lower()
        raw_args = fn_part[paren_idx + 1 :].rstrip(")") if paren_idx >= 0 else ""
        args = [a.strip() for a in raw_args.split(",") if a.strip()] if raw_args else []

        for resolver in self._resolvers:
            if resolver.handles(name):
                return resolver.resolve(name, args, context_entity)

        return value
