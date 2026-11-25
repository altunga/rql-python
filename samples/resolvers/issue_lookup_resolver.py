"""Sample ILookupResolver mapping display values to integer foreign-key IDs."""

from __future__ import annotations

from collections.abc import Iterable

from rql.abstractions.accessors import ILookupResolver


class IssueLookupResolver(ILookupResolver):
    """Resolves status, priority, issuetype, and assignee display names to integer IDs."""

    def __init__(self) -> None:
        self._tables: dict[str, dict[str, int]] = {
            "status": {"open": 1, "in progress": 2, "resolved": 3, "closed": 4},
            "priority": {
                "blocker": 1,
                "critical": 2,
                "high": 3,
                "medium": 4,
                "low": 5,
                "trivial": 6,
            },
            "issuetype": {"bug": 1, "task": 2, "story": 3, "epic": 4},
            "assignee": {"alice": 101, "bob": 102, "eren": 103},
        }

    def is_lookup_field(self, field_name: str) -> bool:
        return field_name.lower() in self._tables

    def resolve(self, field_name: str, display_value: str) -> int | None:
        return self._tables.get(field_name.lower(), {}).get(display_value.lower())

    def resolve_many(self, field_name: str, display_values: Iterable[str]) -> list[int]:
        ids: list[int] = []
        for val in display_values:
            resolved = self.resolve(field_name, val)
            if resolved is not None:
                ids.append(resolved)
        return ids
