"""SQLAlchemy 2.0 ORM model for Issues."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from samples.models.sqlalchemy.base import Base
from samples.models.sqlalchemy.issue_assignee_model import IssueAssigneeModel


class IssueModel(Base):
    """SQLAlchemy 2.0 ORM model representing a searchable Issue."""

    __tablename__ = "issues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    project: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    issuetype_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    issuetype_name: Mapped[str] = mapped_column(String(50), nullable=False)
    status_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    status_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    priority_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    priority_name: Mapped[str] = mapped_column(String(50), nullable=False)
    summary: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    sprint: Mapped[str | None] = mapped_column(String(50), nullable=True)
    votes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    assignees: Mapped[list[IssueAssigneeModel]] = relationship(
        IssueAssigneeModel,
        cascade="all, delete-orphan",
    )
