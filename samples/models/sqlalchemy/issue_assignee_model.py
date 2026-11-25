"""SQLAlchemy 2.0 ORM model for issue assignees (collection relationship)."""

from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from samples.models.sqlalchemy.base import Base


class IssueAssigneeModel(Base):
    """Many-to-one assignee row associated with an IssueModel."""

    __tablename__ = "issue_assignees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    issue_id: Mapped[int] = mapped_column(ForeignKey("issues.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False)
