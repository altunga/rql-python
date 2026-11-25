"""In-memory Issue domain entity for RQL sample queries."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from samples.models.in_memory.user_ref import UserRef


@dataclass
class Issue:
    """Sample Issue entity demonstrating Simple, Lookup, Collection, and Computed RQL fields."""

    Id: int
    Key: str
    ProjectKey: str
    IssueTypeId: int
    IssueTypeName: str
    StatusId: int | None
    StatusName: str | None
    PriorityId: int
    PriorityName: str
    Summary: str
    Description: str | None
    Sprint: str | None
    Votes: int
    Created: datetime
    Updated: datetime
    Assignees: list[UserRef] = field(default_factory=list)
    Labels: list[str] = field(default_factory=list)
