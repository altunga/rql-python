"""End-to-end runnable showcase of the rql library across all features."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from rql import (
    BuiltInRqlFunctionResolver,
    InMemoryRqlExecutor,
    InMemoryRqlSearchService,
    RqlAutocompleteService,
    RqlEngine,
    RqlLexer,
    RqlMetadataService,
    RqlNormalizer,
    RqlParser,
    RqlValidationService,
    SqlAlchemyRqlSearchService,
)
from rql.backends.sqlalchemy import SqlAlchemyRqlExecutor
from samples.configuration import (
    create_in_memory_accessor,
    create_sample_rql_metadata,
    create_sqlalchemy_accessor,
)
from samples.models import Base, Issue, IssueAssigneeModel, IssueModel, UserRef
from samples.resolvers import CurrentUserFunctionResolver, IssueLookupResolver
from samples.visitors import MongoQueryVisitor


def _sample_in_memory_issues() -> list[Issue]:
    return [
        Issue(
            Id=1,
            Key="CRM-101",
            ProjectKey="CRM",
            IssueTypeId=1,
            IssueTypeName="Bug",
            StatusId=1,
            StatusName="Open",
            PriorityId=2,
            PriorityName="Critical",
            Summary="OAuth token refresh error",
            Description="Users get logged out after 15 minutes",
            Sprint="Sprint 2",
            Votes=18,
            Created=datetime(2026, 11, 17, 10, 0, tzinfo=timezone.utc),
            Updated=datetime(2026, 11, 17, 12, 0, tzinfo=timezone.utc),
            Assignees=[UserRef(103, "eren"), UserRef(101, "alice")],
            Labels=["auth", "security"],
        ),
        Issue(
            Id=2,
            Key="CRM-102",
            ProjectKey="CRM",
            IssueTypeId=3,
            IssueTypeName="Story",
            StatusId=2,
            StatusName="In Progress",
            PriorityId=3,
            PriorityName="High",
            Summary="Kanban board column filtering",
            Description="Add RQL search bar to board header",
            Sprint="Sprint 2",
            Votes=9,
            Created=datetime(2026, 11, 16, 14, 0, tzinfo=timezone.utc),
            Updated=datetime(2026, 11, 17, 9, 0, tzinfo=timezone.utc),
            Assignees=[UserRef(102, "bob")],
            Labels=["ui"],
        ),
        Issue(
            Id=3,
            Key="DEV-201",
            ProjectKey="DEV",
            IssueTypeId=2,
            IssueTypeName="Task",
            StatusId=None,
            StatusName=None,
            PriorityId=5,
            PriorityName="Low",
            Summary="Upgrade CI runner image",
            Description=None,
            Sprint="Sprint 1",
            Votes=2,
            Created=datetime(2026, 11, 10, 8, 0, tzinfo=timezone.utc),
            Updated=datetime(2026, 11, 11, 8, 0, tzinfo=timezone.utc),
            Assignees=[],
            Labels=[],
        ),
    ]


def run_showcase() -> None:
    print("=" * 76)
    print("RQL LIBRARY — END-TO-END SHOWCASE")
    print("=" * 76)

    # ── 1. Lexer, Parser, Normalizer & Validation ────────────────────────────
    raw_rql = (
        "project = 'CRM' and (status in ('Open', 'In Progress') or not votes < 5) "
        "and assignee = currentUser() order by votes desc, id asc"
    )
    tokens = RqlLexer(raw_rql).tokenize()
    ast_query = RqlParser(tokens).parse_query()
    normalizer = RqlNormalizer()
    validator = RqlValidationService(normalizer)
    validation = validator.validate(raw_rql)

    print("\n[1] Lexer, Parser, Normalizer & Validation:")
    print(f"  Input RQL      : {raw_rql}")
    print(f"  Token Count    : {len(tokens)}")
    print(f"  Valid?         : {validation.valid}")
    print(f"  Normalized RQL : {validation.normalized_rql}")

    # ── 2. Schema Metadata & Autocomplete ────────────────────────────────────
    schema_meta = create_sample_rql_metadata()
    meta_service = RqlMetadataService(schema_meta)
    autocomplete = RqlAutocompleteService(schema_meta)

    print("\n[2] Schema Metadata & Autocomplete:")
    print(f"  Registered Fields    : {len(meta_service.get_metadata().fields)}")
    print(f"  Suggestions for 'st' : {autocomplete.get_suggestions(None, 'st').suggestions}")
    print(
        f"  Values for priority  : {autocomplete.get_suggestions('priority', 'cr').suggestions}"
    )

    # ── 3. In-Memory Execution (RqlEngine & InMemoryRqlSearchService) ────────
    in_mem_accessor = create_in_memory_accessor()
    lookup_resolver = IssueLookupResolver()
    fixed_clock = lambda: datetime(2026, 11, 17, 15, 0, tzinfo=timezone.utc)
    fn_resolvers: list[
        CurrentUserFunctionResolver[Issue] | BuiltInRqlFunctionResolver[Issue]
    ] = [
        CurrentUserFunctionResolver(current_username="eren", active_sprint="Sprint 2"),
        BuiltInRqlFunctionResolver(clock=fixed_clock),
    ]

    engine = RqlEngine.create_in_memory(
        field_accessors=[in_mem_accessor],
        collection_accessor=in_mem_accessor,
        lookup_resolver=lookup_resolver,
        lookup_field_accessor=in_mem_accessor,
        function_resolvers=fn_resolvers,
        metadata=schema_meta,
    )

    issues = _sample_in_memory_issues()
    matched = engine.execute(
        issues,
        'project = "CRM" AND type = "Bug" AND assignee = currentUser() '
        'AND sprint = openSprints() AND labels = "security" AND text ~ "logged out"',
    )
    print("\n[3] In-Memory Execution (Scalar + Lookup + Collection + Computed + Functions):")
    print(f"  Matched Issue Keys : {[i.Key for i in matched]}")

    in_mem_executor = InMemoryRqlExecutor(
        field_accessors=[in_mem_accessor],
        function_resolvers=fn_resolvers,
        collection_accessor=in_mem_accessor,
        lookup_resolver=lookup_resolver,
        lookup_field_accessor=in_mem_accessor,
    )
    in_mem_search: InMemoryRqlSearchService[Issue, str] = InMemoryRqlSearchService(
        source_provider=lambda: issues,
        executor=in_mem_executor,
        mapper=lambda i: f"{i.Key} ({i.PriorityName}, votes={i.Votes})",
    )
    page = in_mem_search.search('project = "CRM" ORDER BY votes DESC', skip=0, take=10)
    print(f"  Paged Search Total : {page.total}, Items: {page.items}")

    # ── 4. SQLAlchemy 2.0 Execution & Pagination ─────────────────────────────
    sa_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(sa_engine)
    with Session(sa_engine) as session:
        for src in issues:
            session.add(
                IssueModel(
                    id=src.Id,
                    key=src.Key,
                    project=src.ProjectKey,
                    issuetype_id=src.IssueTypeId,
                    issuetype_name=src.IssueTypeName,
                    status_id=src.StatusId,
                    status_name=src.StatusName,
                    priority_id=src.PriorityId,
                    priority_name=src.PriorityName,
                    summary=src.Summary,
                    description=src.Description,
                    sprint=src.Sprint,
                    votes=src.Votes,
                    created=src.Created,
                    assignees=[
                        IssueAssigneeModel(user_id=a.user_id, username=a.username)
                        for a in src.Assignees
                    ],
                )
            )
        session.commit()

        sql_accessor = create_sqlalchemy_accessor()
        sql_executor = SqlAlchemyRqlExecutor(
            field_accessors=[sql_accessor],
            function_resolvers=[
                CurrentUserFunctionResolver(current_username="eren", active_sprint="Sprint 2"),
                BuiltInRqlFunctionResolver(clock=fixed_clock),
            ],
            collection_accessor=sql_accessor,
            lookup_resolver=lookup_resolver,
            lookup_field_accessor=sql_accessor,
        )
        sql_search: SqlAlchemyRqlSearchService[IssueModel, str] = SqlAlchemyRqlSearchService(
            session_factory=lambda: session,
            base_select_provider=lambda: select(IssueModel),
            executor=sql_executor,
            mapper=lambda row: f"{row.key} [{row.status_name}]",
        )
        sql_page = sql_search.search(
            'project = "CRM" AND status IN ("Open", "In Progress") ORDER BY votes DESC',
            skip=0,
            take=5,
        )
        print("\n[4] SQLAlchemy 2.0 Database Execution & Pagination:")
        print(f"  SQL Search Total   : {sql_page.total}, Items: {sql_page.items}")

    # ── 5. Custom AST Visitor (MongoQueryVisitor) ────────────────────────────
    mongo_visitor = MongoQueryVisitor()
    assert ast_query.where is not None
    mongo_filter = ast_query.where.accept(mongo_visitor)
    print("\n[5] Custom AST Visitor (MongoDB Filter Translation):")
    print(f"  Mongo Filter Dict  : {mongo_filter}")
    print("=" * 76)


if __name__ == "__main__":
    run_showcase()
