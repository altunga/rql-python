"""Unit tests for BuiltInRqlFunctionResolver and FunctionResolverChain."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone

from rql.abstractions.functions import IRqlFunctionResolver
from rql.functions.builtin_resolver import (
    BuiltInRqlFunctionResolver,
    FunctionResolverChain,
)


def _fixed_clock() -> datetime:
    # Wednesday, 2026-11-18 15:30:00 UTC (Monday of that week is 2026-11-16)
    return datetime(2026, 11, 18, 15, 30, 0, tzinfo=timezone.utc)


def test_builtin_function_resolver_date_and_member_functions() -> None:
    resolver: BuiltInRqlFunctionResolver[object] = BuiltInRqlFunctionResolver(clock=_fixed_clock)

    assert resolver.handles("NOW") is True
    assert resolver.handles("unknownFn") is False

    assert resolver.resolve("now", []) == "2026-11-18T15:30:00+00:00"
    assert resolver.resolve("startOfDay", []) == "2026-11-18T00:00:00+00:00"
    assert resolver.resolve("startOfDay", ["-1"]) == "2026-11-17T00:00:00+00:00"
    assert resolver.resolve("endOfDay", []) == "2026-11-18T23:59:59+00:00"
    assert resolver.resolve("startOfWeek", []) == "2026-11-16T00:00:00+00:00"
    assert resolver.resolve("endOfWeek", []) == "2026-11-22T23:59:59+00:00"
    assert resolver.resolve("startOfMonth", []) == "2026-11-01T00:00:00+00:00"
    assert resolver.resolve("endOfMonth", []) == "2026-11-30T23:59:59+00:00"
    assert resolver.resolve("startOfYear", []) == "2026-01-01T00:00:00+00:00"
    assert resolver.resolve("endOfYear", []) == "2026-12-31T23:59:59+00:00"
    assert resolver.resolve("lastLogin", []) == "2026-11-18T07:30:00+00:00"
    assert resolver.resolve("membersOf", ["developers"]) == "developers"
    assert resolver.resolve("membersOf", []) == ""


class _CustomUserResolver(IRqlFunctionResolver[object]):
    def handles(self, function_name: str) -> bool:
        return function_name.lower() == "currentuser"

    def resolve(
        self,
        function_name: str,
        args: Sequence[str],
        context_entity: object | None = None,
    ) -> str:
        return "eren"


def test_function_resolver_chain_delegation() -> None:
    chain: FunctionResolverChain[object] = FunctionResolverChain(
        [_CustomUserResolver(), BuiltInRqlFunctionResolver(clock=_fixed_clock)]
    )
    assert chain.resolve_token("__fn:currentUser()") == "eren"
    assert chain.resolve_token("__fn:now()") == "2026-11-18T15:30:00+00:00"
    assert chain.resolve_token("plain_value") == "plain_value"
    assert chain.resolve_token("__fn:unhandled()") == "__fn:unhandled()"
