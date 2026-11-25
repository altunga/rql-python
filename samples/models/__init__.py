"""Sample domain models group (both in-memory and SQLAlchemy 2.0)."""

from samples.models.in_memory import Issue, UserRef
from samples.models.sqlalchemy import Base, IssueAssigneeModel, IssueModel

__all__ = ["Base", "Issue", "IssueAssigneeModel", "IssueModel", "UserRef"]
