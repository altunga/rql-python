"""RQL schema metadata container (fields, operators, functions)."""

from __future__ import annotations

from collections.abc import Iterable

from rql.metadata.schema.rql_field import RqlField
from rql.metadata.schema.rql_function import RqlFunction


def _default_operators() -> list[str]:
    return [
        "=",
        "!=",
        "<",
        "<=",
        ">",
        ">=",
        "~",
        "!~",
        "IN",
        "NOT IN",
        "IS",
        "IS NOT",
        "WAS",
        "WAS IN",
        "WAS NOT",
        "WAS NOT IN",
        "CHANGED",
    ]


def _default_functions() -> list[RqlFunction]:
    return [
        RqlFunction("membersOf", "user", 'membersOf("group") — members of a group'),
        RqlFunction("now", "date", "Current UTC date and time"),
        RqlFunction("startOfDay", "date", 'Start of today. Optional offset: startOfDay("-1")'),
        RqlFunction("endOfDay", "date", "End of today"),
        RqlFunction("startOfWeek", "date", "Start of the current week"),
        RqlFunction("endOfWeek", "date", "End of the current week"),
        RqlFunction("startOfMonth", "date", "Start of the current month"),
        RqlFunction("endOfMonth", "date", "End of the current month"),
        RqlFunction("startOfYear", "date", "Start of the current year"),
        RqlFunction("endOfYear", "date", "End of the current year"),
        RqlFunction("lastLogin", "date", "Date/time of the current user's last login"),
    ]


class RqlMetadata:
    """Domain-agnostic RQL schema metadata container (fields, operators, and functions)."""

    def __init__(
        self,
        fields: Iterable[RqlField] | None = None,
        operators: Iterable[str] | None = None,
        functions: Iterable[RqlFunction] | None = None,
    ) -> None:
        self._fields = list(fields) if fields is not None else []
        self._operators = (
            list(operators) if operators is not None else _default_operators()
        )
        self._functions = (
            list(functions) if functions is not None else _default_functions()
        )

    @property
    def fields(self) -> list[RqlField]:
        return list(self._fields)

    @property
    def operators(self) -> list[str]:
        return list(self._operators)

    @property
    def functions(self) -> list[RqlFunction]:
        return list(self._functions)

    def add_field(self, field: RqlField) -> RqlMetadata:
        """Registers a schema field definition and returns self for fluent chaining."""
        self._fields.append(field)
        return self

    def add_function(self, function: RqlFunction) -> RqlMetadata:
        """Registers a schema function definition and returns self for fluent chaining."""
        self._functions.append(function)
        return self

    def get_field(self, name: str) -> RqlField | None:
        """Resolves a field definition by name (case-insensitive)."""
        target = name.lower()
        for f in self._fields:
            if f.name.lower() == target:
                return f
        return None
