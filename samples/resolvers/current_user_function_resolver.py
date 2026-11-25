"""Sample custom IRqlFunctionResolver for currentUser() and openSprints()."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TypeVar

from rql.abstractions.functions import IRqlFunctionResolver

T = TypeVar("T")


class CurrentUserFunctionResolver(IRqlFunctionResolver[T]):
    """Resolves custom domain RQL functions such as currentUser() and openSprints()."""

    def __init__(self, current_username: str = "eren", active_sprint: str = "Sprint 2") -> None:
        self._current_username = current_username
        self._active_sprint = active_sprint

    def handles(self, function_name: str) -> bool:
        return function_name.lower() in ("currentuser", "opensprints")

    def resolve(
        self,
        function_name: str,
        args: Sequence[str],
        context_entity: T | None = None,
    ) -> str:
        name = function_name.lower()
        if name == "currentuser":
            return self._current_username
        if name == "opensprints":
            return self._active_sprint
        return ""
