"""Unit tests for InMemoryRqlExecutor, Operator Strategies, InMemoryRqlSearchService, and RqlEngine."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime, timezone

from rql.abstractions.accessors import ILookupResolver
from rql.backends.in_memory.executor import InMemoryRqlExecutor
from rql.facade import RqlEngine
from rql.functions.builtin_resolver import BuiltInRqlFunctionResolver
from rql.metadata.builder import FieldMetadataBuilder
from rql.metadata.dynamic_accessor import DynamicEntityFieldAccessor
from rql.parser.rql_parser import RqlParser
from rql.services.search_service import InMemoryRqlSearchService


@dataclass
class UserRef:
    user_id: int
    username: str


@dataclass
class Issue:
    id: int
    project: str
    status_id: int | None
    status_name: str | None
    priority_id: int
    priority_name: str
    summary: str
    description: str | None
    votes: int
    created: datetime
    assignees: list[UserRef] = field(default_factory=list)
    watchers: list[str] = field(default_factory=list)


class FakeLookupResolver(ILookupResolver):
    def __init__(self) -> None:
        self._tables: dict[str, dict[str, int]] = {
            "status": {"open": 1, "in progress": 2, "closed": 3},
            "priority": {"high": 10, "medium": 20, "low": 30},
            "assignee": {"alice": 100, "bob": 200},
            "watcher": {"alice": 100},
        }

    def is_lookup_field(self, field_name: str) -> bool:
        return field_name.lower() in self._tables

    def resolve(self, field_name: str, display_value: str) -> int | None:
        table = self._tables.get(field_name.lower(), {})
        return table.get(display_value.lower())

    def resolve_many(self, field_name: str, display_values: Iterable[str]) -> list[int]:
        result: list[int] = []
        for val in display_values:
            resolved = self.resolve(field_name, val)
            if resolved is not None:
                result.append(resolved)
        return result


def _build_accessor() -> DynamicEntityFieldAccessor[Issue]:
    builder: FieldMetadataBuilder[Issue] = FieldMetadataBuilder()
    registry = (
        builder.add_simple_field("id", lambda i: i.id)
        .add_simple_field("project", lambda i: i.project)
        .add_simple_field("summary", lambda i: i.summary)
        .add_simple_field("description", lambda i: i.description)
        .add_simple_field("votes", lambda i: i.votes)
        .add_simple_field("created", lambda i: i.created)
        .add_lookup_field("status", lambda i: i.status_name, lambda i: i.status_id or 0)
        .add_lookup_field("priority", lambda i: i.priority_name, lambda i: i.priority_id)
        .add_collection_field(
            "assignee",
            scalar_expression=lambda i: i.assignees,
            collection_contains_builder=lambda val: (
                lambda i: any(a.username.lower() == val.lower() for a in i.assignees)
            ),
            collection_contains_substring_builder=lambda val: (
                lambda i: any(val.lower() in a.username.lower() for a in i.assignees)
            ),
            collection_is_empty_expression=lambda i: len(i.assignees) == 0,
            collection_contains_by_id_builder=lambda uid: (
                lambda i: any(a.user_id == uid for a in i.assignees)
            ),
            collection_contains_by_ids_builder=lambda uids: (
                lambda i: any(a.user_id in uids for a in i.assignees)
            ),
        )
        # Collection field WITHOUT by_id builders to verify string fallback (Review Focus #5)
        .add_collection_field(
            "watcher",
            scalar_expression=lambda i: i.watchers,
            collection_contains_builder=lambda val: (
                lambda i: any(w.lower() == val.lower() for w in i.watchers)
            ),
            collection_contains_substring_builder=lambda val: (
                lambda i: any(val.lower() in w.lower() for w in i.watchers)
            ),
            collection_is_empty_expression=lambda i: len(i.watchers) == 0,
        )
        .add_computed_field("text", lambda i: f"{i.summary} {i.description or ''}")
        .build()
    )
    return DynamicEntityFieldAccessor(registry)


def _sample_issues() -> list[Issue]:
    return [
        Issue(
            id=1,
            project="CRM",
            status_id=1,
            status_name="Open",
            priority_id=10,
            priority_name="High",
            summary="Login OAuth error",
            description="Token refresh fails",
            votes=12,
            created=datetime(2026, 11, 18, 10, 0, tzinfo=timezone.utc),
            assignees=[UserRef(100, "alice")],
            watchers=["alice", "charlie"],
        ),
        Issue(
            id=2,
            project="CRM",
            status_id=2,
            status_name="In Progress",
            priority_id=20,
            priority_name="Medium",
            summary="Dashboard chart slow",
            description=None,
            votes=3,
            created=datetime(2026, 11, 15, 9, 0, tzinfo=timezone.utc),
            assignees=[UserRef(200, "bob")],
            watchers=[],
        ),
        Issue(
            id=3,
            project="SUP",
            status_id=None,
            status_name=None,
            priority_id=30,
            priority_name="Low",
            summary="Export CSV encoding",
            description="UTF-8 BOM issue",
            votes=7,
            created=datetime(2026, 11, 10, 8, 0, tzinfo=timezone.utc),
            assignees=[],
            watchers=["bob"],
        ),
    ]


def _make_executor() -> InMemoryRqlExecutor[Issue]:
    accessor = _build_accessor()
    clock = lambda: datetime(2026, 11, 18, 15, 0, tzinfo=timezone.utc)
    return InMemoryRqlExecutor(
        field_accessors=[accessor],
        function_resolvers=[BuiltInRqlFunctionResolver(clock=clock)],
        collection_accessor=accessor,
        lookup_resolver=FakeLookupResolver(),
        lookup_field_accessor=accessor,
    )


def test_scalar_filtering_and_ordering() -> None:
    executor = _make_executor()
    issues = _sample_issues()

    # Equality, contains, numeric compare, and ORDER BY
    res = executor.execute(
        issues,
        RqlParser.parse('project = "CRM" AND votes >= 3 ORDER BY votes ASC'),
    )
    assert [i.id for i in res] == [2, 1]

    # Computed field ~ and !~
    res_text = executor.execute(issues, RqlParser.parse('text ~ "token" AND summary !~ "slow"'))
    assert [i.id for i in res_text] == [1]

    # Date function comparison (startOfDay is 2026-11-18T00:00:00+00:00)
    res_date = executor.execute(issues, RqlParser.parse("created >= startOfDay()"))
    assert [i.id for i in res_date] == [1]

    # IS EMPTY and IS NOT EMPTY on scalar
    res_null = executor.execute(issues, RqlParser.parse("description IS EMPTY"))
    assert [i.id for i in res_null] == [2]
    res_not_null = executor.execute(issues, RqlParser.parse("description IS NOT NULL"))
    assert [i.id for i in res_not_null] == [1, 3]


def test_lookup_path_and_unresolved_lookup_semantics() -> None:
    executor = _make_executor()
    issues = _sample_issues()

    # Direct FK equality and IN
    assert [i.id for i in executor.execute(issues, RqlParser.parse('status = "Open"'))] == [1]
    assert [
        i.id for i in executor.execute(issues, RqlParser.parse('status IN ("Open", "In Progress")'))
    ] == [1, 2]

    # Unresolved lookup: = and IN return False (0 matches); != and NOT IN return True (all matches)
    assert executor.execute(issues, RqlParser.parse('status = "NonExistent"')) == []
    assert executor.execute(issues, RqlParser.parse('status IN ("NonExistent")')) == []
    assert len(executor.execute(issues, RqlParser.parse('status != "NonExistent"'))) == 3
    assert len(executor.execute(issues, RqlParser.parse('status NOT IN ("NonExistent")'))) == 3

    # Lookup ~ falls back to scalar string contains
    assert [i.id for i in executor.execute(issues, RqlParser.parse('status ~ "progress"'))] == [2]

    # Lookup IS EMPTY bypasses FK integer lookup and checks null/empty (Review Focus #3)
    assert [i.id for i in executor.execute(issues, RqlParser.parse("status IS EMPTY"))] == [3]


def test_collection_path_id_and_string_fallback() -> None:
    executor = _make_executor()
    issues = _sample_issues()

    # ID-based resolution for assignee = "alice" (user_id == 100)
    assert [i.id for i in executor.execute(issues, RqlParser.parse('assignee = "alice"'))] == [1]
    assert [
        i.id for i in executor.execute(issues, RqlParser.parse('assignee IN ("alice", "bob")'))
    ] == [1, 2]
    assert [
        i.id for i in executor.execute(issues, RqlParser.parse('assignee NOT IN ("alice")'))
    ] == [2, 3]

    # Substring ~ and empty checks
    assert [i.id for i in executor.execute(issues, RqlParser.parse('assignee ~ "ob"'))] == [2]
    assert [i.id for i in executor.execute(issues, RqlParser.parse("assignee IS EMPTY"))] == [3]
    assert [
        i.id for i in executor.execute(issues, RqlParser.parse("assignee IS NOT EMPTY"))
    ] == [1, 2]

    # Fallback to string matching when lookup has no by_id builder ("watcher" field)
    # or when lookup value is unknown ("charlie") (Review Focus #5)
    assert [i.id for i in executor.execute(issues, RqlParser.parse('watcher = "alice"'))] == [1]
    assert [i.id for i in executor.execute(issues, RqlParser.parse('watcher = "charlie"'))] == [1]


def test_search_service_and_rql_engine_facade() -> None:
    issues = _sample_issues()
    executor = _make_executor()
    search_service = InMemoryRqlSearchService(
        source_provider=lambda: issues,
        executor=executor,
        mapper=lambda i: i.id,
    )
    page = search_service.search('project = "CRM" ORDER BY id ASC', skip=0, take=1)
    assert page.total == 2
    assert page.total_pages == 2
    assert page.items == [1]

    # Negative skip is clamped to 0
    neg_page = search_service.search('project = "CRM" ORDER BY id ASC', skip=-5, take=1)
    assert neg_page.skip == 0
    assert neg_page.items == [1]

    engine = RqlEngine.create_in_memory(
        field_accessors=[_build_accessor()],
        collection_accessor=_build_accessor(),
        lookup_resolver=FakeLookupResolver(),
        lookup_field_accessor=_build_accessor(),
    )
    validation = engine.validate("project = 'CRM'")
    assert validation.valid is True
    assert validation.normalized_rql == 'project = "CRM"'
    filtered = engine.execute(issues, "project = 'CRM'")
    assert len(filtered) == 2
