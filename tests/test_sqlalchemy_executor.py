"""Integration tests for SqlAlchemyRqlExecutor and SqlAlchemyRqlSearchService with SQLite."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone

import pytest
from sqlalchemy import DateTime, ForeignKey, Integer, String, create_engine, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship

from rql.abstractions.accessors import ILookupResolver
from rql.backends.sqlalchemy.executor import SqlAlchemyRqlExecutor
from rql.functions.builtin_resolver import BuiltInRqlFunctionResolver
from rql.metadata.builder import FieldMetadataBuilder
from rql.metadata.dynamic_accessor import DynamicEntityFieldAccessor
from rql.parser.rql_parser import RqlParser
from rql.services.search_service import SqlAlchemyRqlSearchService


class Base(DeclarativeBase):
    pass


class IssueAssigneeModel(Base):
    __tablename__ = "issue_assignees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    issue_id: Mapped[int] = mapped_column(ForeignKey("issues.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    username: Mapped[str] = mapped_column(String(100), nullable=False)


class IssueModel(Base):
    __tablename__ = "issues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project: Mapped[str] = mapped_column(String(50), nullable=False)
    status_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    summary: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    votes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    assignees: Mapped[list[IssueAssigneeModel]] = relationship(
        IssueAssigneeModel,
        cascade="all, delete-orphan",
    )


class SqlLookupResolver(ILookupResolver):
    def __init__(self) -> None:
        self._tables: dict[str, dict[str, int]] = {
            "status": {"open": 1, "in progress": 2, "closed": 3},
            "assignee": {"alice": 100, "bob": 200},
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


def _build_sql_accessor() -> DynamicEntityFieldAccessor[IssueModel]:
    builder: FieldMetadataBuilder[IssueModel] = FieldMetadataBuilder()
    registry = (
        builder.add_simple_field("id", IssueModel.id)
        .add_simple_field("project", IssueModel.project)
        .add_simple_field("summary", IssueModel.summary)
        .add_simple_field("description", IssueModel.description)
        .add_simple_field("votes", IssueModel.votes)
        .add_simple_field("created", IssueModel.created)
        .add_lookup_field("status", IssueModel.status_name, IssueModel.status_id)
        .add_collection_field(
            "assignee",
            scalar_expression=IssueModel.assignees,
            collection_contains_builder=lambda val: IssueModel.assignees.any(
                func.lower(IssueAssigneeModel.username) == val.lower()
            ),
            collection_contains_substring_builder=lambda val: IssueModel.assignees.any(
                func.lower(IssueAssigneeModel.username).contains(val.lower())
            ),
            collection_is_empty_expression=~IssueModel.assignees.any(),
            collection_contains_by_id_builder=lambda uid: IssueModel.assignees.any(
                IssueAssigneeModel.user_id == uid
            ),
            collection_contains_by_ids_builder=lambda uids: IssueModel.assignees.any(
                IssueAssigneeModel.user_id.in_(uids)
            ),
        )
        .add_computed_field(
            "text",
            func.coalesce(IssueModel.summary, "")
            + " "
            + func.coalesce(IssueModel.description, ""),
        )
        .build()
    )
    return DynamicEntityFieldAccessor(registry)


@pytest.fixture()
def db_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    session.add_all(
        [
            IssueModel(
                id=1,
                project="CRM",
                status_id=1,
                status_name="Open",
                summary="Login bug",
                description="OAuth token expired",
                votes=15,
                created=datetime(2026, 11, 18, 12, 0, tzinfo=timezone.utc),
                assignees=[IssueAssigneeModel(user_id=100, username="alice")],
            ),
            IssueModel(
                id=2,
                project="CRM",
                status_id=2,
                status_name="In Progress",
                summary="Kanban drag lag",
                description=None,
                votes=4,
                created=datetime(2026, 11, 15, 9, 0, tzinfo=timezone.utc),
                assignees=[IssueAssigneeModel(user_id=200, username="bob")],
            ),
            IssueModel(
                id=3,
                project="DEV",
                status_id=None,
                status_name=None,
                summary="CI pipeline timeout",
                description="Docker layer cache miss",
                votes=8,
                created=datetime(2026, 11, 10, 8, 0, tzinfo=timezone.utc),
                assignees=[],
            ),
        ]
    )
    session.commit()
    return session


def _make_sql_executor() -> SqlAlchemyRqlExecutor[IssueModel]:
    accessor = _build_sql_accessor()
    clock = lambda: datetime(2026, 11, 18, 15, 0, tzinfo=timezone.utc)
    return SqlAlchemyRqlExecutor(
        field_accessors=[accessor],
        function_resolvers=[BuiltInRqlFunctionResolver(clock=clock)],
        collection_accessor=accessor,
        lookup_resolver=SqlLookupResolver(),
        lookup_field_accessor=accessor,
    )


def test_sqlalchemy_scalar_lookup_collection_and_ordering(db_session: Session) -> None:
    executor = _make_sql_executor()

    # 1. Scalar + numeric compare + ORDER BY
    stmt1 = executor.execute(
        select(IssueModel),
        RqlParser.parse('project = "CRM" AND votes >= 4 ORDER BY votes ASC'),
    )
    rows1 = db_session.scalars(stmt1).all()
    assert [r.id for r in rows1] == [2, 1]

    # 2. Computed field ~
    stmt2 = executor.execute(
        select(IssueModel),
        RqlParser.parse('text ~ "oauth"'),
    )
    assert [r.id for r in db_session.scalars(stmt2).all()] == [1]

    # 3. Lookup FK direct comparison & IS EMPTY
    stmt3 = executor.execute(
        select(IssueModel),
        RqlParser.parse('status = "Open"'),
    )
    assert [r.id for r in db_session.scalars(stmt3).all()] == [1]

    stmt_empty_lookup = executor.execute(
        select(IssueModel),
        RqlParser.parse("status IS EMPTY"),
    )
    assert [r.id for r in db_session.scalars(stmt_empty_lookup).all()] == [3]

    # Unresolved lookup: = -> 0 rows, != -> 3 rows
    assert (
        db_session.scalars(
            executor.execute(select(IssueModel), RqlParser.parse('status = "Unknown"'))
        ).all()
        == []
    )
    assert (
        len(
            db_session.scalars(
                executor.execute(
                    select(IssueModel), RqlParser.parse('status != "Unknown"')
                )
            ).all()
        )
        == 3
    )

    # 4. Collection by ID, substring ~, and IS EMPTY
    stmt_coll_id = executor.execute(
        select(IssueModel),
        RqlParser.parse('assignee = "alice"'),
    )
    assert [r.id for r in db_session.scalars(stmt_coll_id).all()] == [1]

    stmt_coll_sub = executor.execute(
        select(IssueModel),
        RqlParser.parse('assignee ~ "ob"'),
    )
    assert [r.id for r in db_session.scalars(stmt_coll_sub).all()] == [2]

    stmt_coll_empty = executor.execute(
        select(IssueModel),
        RqlParser.parse("assignee IS EMPTY"),
    )
    assert [r.id for r in db_session.scalars(stmt_coll_empty).all()] == [3]


def test_sqlalchemy_search_service_pagination(db_session: Session) -> None:
    executor = _make_sql_executor()
    service: SqlAlchemyRqlSearchService[IssueModel, int] = SqlAlchemyRqlSearchService(
        session_factory=lambda: db_session,
        base_select_provider=lambda: select(IssueModel),
        executor=executor,
        mapper=lambda issue: issue.id,
    )

    page = service.search('project = "CRM" ORDER BY id DESC', skip=0, take=1)
    assert page.total == 2
    assert page.total_pages == 2
    assert page.items == [2]


def test_sqlalchemy_unknown_field_and_nullable_lookup_and_collection_fallback(
    db_session: Session,
) -> None:
    executor = _make_sql_executor()

    # Issue #1: Unknown field = "x" must return 0 rows (false), != "x" and IS EMPTY return all rows
    assert (
        db_session.scalars(
            executor.execute(
                select(IssueModel), RqlParser.parse('unknownfield = "x"')
            )
        ).all()
        == []
    )
    assert (
        len(
            db_session.scalars(
                executor.execute(
                    select(IssueModel), RqlParser.parse('unknownfield != "x"')
                )
            ).all()
        )
        == 3
    )
    assert (
        len(
            db_session.scalars(
                executor.execute(
                    select(IssueModel), RqlParser.parse("unknownfield IS EMPTY")
                )
            ).all()
        )
        == 3
    )

    # Issue #2: Nullable lookup FK != and NOT IN must include NULL rows (Issue 3 has status_id=None)
    not_open_ids = [
        r.id
        for r in db_session.scalars(
            executor.execute(
                select(IssueModel),
                RqlParser.parse('status != "Open" ORDER BY id ASC'),
            )
        ).all()
    ]
    assert not_open_ids == [2, 3]

    not_in_open_ids = [
        r.id
        for r in db_session.scalars(
            executor.execute(
                select(IssueModel),
                RqlParser.parse('status NOT IN ("Open") ORDER BY id ASC'),
            )
        ).all()
    ]
    assert not_in_open_ids == [2, 3]

    # Issue #4 / Review Focus #5: Collection fallback to string matching when lookup ID is unknown
    # Add an assignee "charlie" (not in SqlLookupResolver) to Issue 3 and query assignee = "charlie"
    issue3 = db_session.get(IssueModel, 3)
    assert issue3 is not None
    issue3.assignees.append(IssueAssigneeModel(user_id=999, username="charlie"))
    db_session.commit()

    charlie_ids = [
        r.id
        for r in db_session.scalars(
            executor.execute(
                select(IssueModel),
                RqlParser.parse('assignee = "charlie"'),
            )
        ).all()
    ]
    assert charlie_ids == [3]

    # Date function & boolean operators in SQLAlchemy
    recent_ids = [
        r.id
        for r in db_session.scalars(
            executor.execute(
                select(IssueModel),
                RqlParser.parse('created >= startOfDay() AND NOT project = "DEV"'),
            )
        ).all()
    ]
    assert recent_ids == [1]
