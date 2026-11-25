"""Built-in RQL date and user function resolver."""

from __future__ import annotations

import calendar
from collections.abc import Callable, Sequence
from datetime import datetime, timedelta, timezone
from typing import Generic, TypeVar

T = TypeVar("T")

_SUPPORTED_NAMES: frozenset[str] = frozenset(
    {
        "membersof",
        "now",
        "startofday",
        "endofday",
        "startofweek",
        "endofweek",
        "startofmonth",
        "endofmonth",
        "startofyear",
        "endofyear",
        "lastlogin",
    }
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class BuiltInRqlFunctionResolver(Generic[T]):
    """Resolves built-in RQL date/user functions (now, startOfDay, etc.)."""

    def __init__(self, clock: Callable[[], datetime] | None = None) -> None:
        self._clock = clock or _utc_now

    def handles(self, function_name: str) -> bool:
        return function_name.lower() in _SUPPORTED_NAMES

    def resolve(
        self,
        function_name: str,
        args: Sequence[str],
        context_entity: T | None = None,
    ) -> str:
        name = function_name.lower()
        now = self._clock()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        offset_days = self._parse_day_offset(args)

        if name == "membersof":
            return args[0] if len(args) > 0 else ""
        if name == "now":
            return now.isoformat()
        if name == "startofday":
            return (today_start + timedelta(days=offset_days)).isoformat()
        if name == "endofday":
            return (
                today_start + timedelta(days=1 + offset_days) - timedelta(seconds=1)
            ).isoformat()
        if name == "startofweek":
            start_week = self._start_of_week(today_start) + timedelta(weeks=offset_days)
            return start_week.isoformat()
        if name == "endofweek":
            start_week = self._start_of_week(today_start) + timedelta(weeks=offset_days)
            return (start_week + timedelta(days=7) - timedelta(seconds=1)).isoformat()
        if name == "startofmonth":
            first_of_month = today_start.replace(day=1)
            return first_of_month.isoformat()
        if name == "endofmonth":
            _, last_day = calendar.monthrange(today_start.year, today_start.month)
            end_month = today_start.replace(
                day=last_day, hour=23, minute=59, second=59
            )
            return end_month.isoformat()
        if name == "startofyear":
            return today_start.replace(month=1, day=1).isoformat()
        if name == "endofyear":
            return today_start.replace(
                month=12, day=31, hour=23, minute=59, second=59
            ).isoformat()
        if name == "lastlogin":
            return (now - timedelta(hours=8)).isoformat()
        return ""

    @staticmethod
    def _start_of_week(today_start: datetime) -> datetime:
        return today_start - timedelta(days=today_start.weekday())

    @staticmethod
    def _parse_day_offset(args: Sequence[str]) -> int:
        if not args:
            return 0
        try:
            return int(args[0].strip())
        except ValueError:
            return 0
