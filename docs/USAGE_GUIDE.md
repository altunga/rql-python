# `rql` — Developer Usage Guide

`rql` is a Python query engine for **RQL (Resource Query Language)**—a JQL-inspired query syntax for filtering, sorting, validating, and autocompleting structured records. It supports both **in-memory Python collections** (dataclasses, Pydantic models, plain objects) and **SQLAlchemy 2.0 ORM queries**.

---

## Table of Contents

1. [Installation](#1-installation)
2. [RQL Syntax Reference](#2-rql-syntax-reference)
3. [Parsing, Validation, Normalization & Autocomplete](#3-parsing-validation-normalization--autocomplete)
4. [Configuring Entity Fields & Lookups](#4-configuring-entity-fields--lookups)
5. [In-Memory Query Execution & Pagination](#5-in-memory-query-execution--pagination)
6. [SQLAlchemy 2.0 Query Execution & Pagination](#6-sqlalchemy-20-query-execution--pagination)
7. [Customizing Functions & Operators](#7-customizing-functions--operators)
8. [API Reference Summary](#8-api-reference-summary)

---

## 1. Installation

### Core Package (Zero Dependencies — In-Memory Usage)
```bash
pip install rql
# Or from local source:
pip install -e .
```

### With SQLAlchemy 2.0 Support
```bash
pip install "rql[sqlalchemy]"
```

---

## 2. RQL Syntax Reference

### Operators

| Operator | Meaning | Example |
|---|---|---|
| `=` / `!=` | Case-insensitive equality / inequality | `project = "CRM"`, `status != "Closed"` |
| `<` `<=` `>` `>=` | Numeric, ISO-8601 date/time, or string comparison | `votes >= 10`, `created >= "2026-01-01"` |
| `~` / `!~` | Case-insensitive substring contains / does not contain | `summary ~ "login"`, `text !~ "wip"` |
| `IN` / `NOT IN` | Matches / does not match any value in list | `priority IN ("High", "Critical")` |
| `IS` / `IS NOT` | Null or empty check (`EMPTY` or `NULL`) | `assignee IS EMPTY`, `description IS NOT NULL` |
| `WAS` / `WAS NOT` | Historical value equality / inequality | `status WAS "Open"` |
| `WAS IN` / `WAS NOT IN` | Historical value list membership | `status WAS IN ("Open", "Reopened")` |
| `CHANGED` | Field value changed check | `status CHANGED` |

### Boolean Logic & Grouping
- Operator precedence (highest to lowest): `NOT` $\rightarrow$ `AND` $\rightarrow$ `OR`.
- Use parentheses `(...)` to group expressions explicitly:
  ```sql
  project = "CRM" AND (status = "Open" OR priority IN ("High", "Blocker")) AND NOT assignee IS EMPTY
  ```

### Sorting (`ORDER BY`)
Append `ORDER BY` followed by one or more field names and optional `ASC` (default) or `DESC`:
```sql
project = "CRM" ORDER BY created DESC, priority ASC
```

### Built-In Functions
- `now()` — Current UTC timestamp in ISO-8601 format.
- `startOfDay()`, `startOfDay("-1")`, `endOfDay()` — Start or end of the current UTC day (supports optional day offset).
- `startOfWeek()`, `endOfWeek()` — Start (Monday `00:00:00`) or end (Sunday `23:59:59`) of the current UTC week.
- `startOfMonth()`, `endOfMonth()` — Start or end of the current UTC month.
- `startOfYear()`, `endOfYear()` — Start or end of the current UTC year.
- `lastLogin()` — 8 hours prior to current UTC timestamp.
- `membersOf("group-name")` — Resolves the group argument.

---

## 3. Parsing, Validation, Normalization & Autocomplete

You can parse, validate, normalize, and generate autocomplete suggestions without configuring any database or entity models.

```python
from rql import (
    RqlAutocompleteService,
    RqlMetadata,
    RqlMetadataService,
    RqlNormalizer,
    RqlParser,
    RqlValidationService,
)

# 1. Parse an RQL string into an AST (RqlQuery)
query = RqlParser.parse("Project = 'CRM' and Status in ('Open', 'In Progress') order by created desc")

# 2. Normalize a parsed query into canonical RQL
normalizer = RqlNormalizer()
canonical = normalizer.normalize(query)
print(canonical)
# Output: (project = "CRM" AND status IN ("Open", "In Progress")) ORDER BY created DESC

# 3. Validate user input
validator = RqlValidationService(normalizer)
result = validator.validate("project = 'CRM'")
if result.valid:
    print("Valid RQL:", result.normalized_rql)
else:
    print("Syntax errors:", result.errors)

# 4. Schema metadata & autocomplete suggestions
metadata = RqlMetadata()  # Uses default schema, or pass custom RqlField / RqlFunction lists
metadata_service = RqlMetadataService(metadata)
autocomplete_service = RqlAutocompleteService(metadata)

# Suggest field names and functions starting with "st"
print(autocomplete_service.get_suggestions(field=None, query="st").suggestions)
# Output: ['status', 'startOfDay()', 'startOfWeek()', 'startOfMonth()', 'startOfYear()']

# Suggest allowed values for a specific field
print(autocomplete_service.get_suggestions(field="priority", query="cr").suggestions)
# Output: ['Critical']

# Suggest date functions when autocompleting a date field
print(autocomplete_service.get_suggestions(field="created", query="startOf").suggestions)
# Output: ['startOfDay()', 'startOfWeek()', 'startOfMonth()', 'startOfYear()']
```

---

## 4. Configuring Entity Fields & Lookups

To execute RQL queries against your data models, configure a `FieldMetadataRegistry` using `FieldMetadataBuilder` and wrap it in `DynamicEntityFieldAccessor`.

### Field Types Supported by `FieldMetadataBuilder`
1. **Simple Fields (`add_simple_field`):** Standard scalar attributes (`str`, `int`, `float`, `datetime`).
2. **Lookup Fields (`add_lookup_field`):** Foreign-key backed fields (e.g., `status = "Open"`). Resolves display names to integer IDs via `ILookupResolver` and compares against the integer FK directly (`status_id == 1`) without requiring table joins.
3. **Collection Fields (`add_collection_field`):** One-to-many or many-to-many collections (e.g., `assignee = "alice"`). Supports both ID-based matching and string/substring matching.
4. **Computed Fields (`add_computed_field`):** Calculated expressions combining multiple properties (e.g., `text` searching across `summary` and `description`).

### Automatic Field Naming Rules
When you omit the explicit field name string in `FieldMetadataBuilder`:
- Property names are converted to `camelCase` (`ProjectKey` $\rightarrow$ `projectKey`).
- Lookup FK suffixes (`Id`) are stripped automatically (`StatusId` $\rightarrow$ `status`).
- Plural collection names are singularized (`Assignees` $\rightarrow$ `assignee`, `Categories` $\rightarrow$ `category`).

### Implementing `ILookupResolver`

```python
from collections.abc import Iterable
from rql import ILookupResolver


class IssueLookupResolver(ILookupResolver):
    """Maps display values (e.g. 'Open', 'High', 'alice') to integer foreign-key IDs."""

    def __init__(self) -> None:
        self._lookups: dict[str, dict[str, int]] = {
            "status": {"open": 1, "in progress": 2, "closed": 3},
            "priority": {"low": 10, "medium": 20, "high": 30},
            "assignee": {"alice": 101, "bob": 102},
        }

    def is_lookup_field(self, field_name: str) -> bool:
        return field_name.lower() in self._lookups

    def resolve(self, field_name: str, display_value: str) -> int | None:
        return self._lookups.get(field_name.lower(), {}).get(display_value.lower())

    def resolve_many(self, field_name: str, display_values: Iterable[str]) -> list[int]:
        ids: list[int] = []
        for val in display_values:
            resolved = self.resolve(field_name, val)
            if resolved is not None:
                ids.append(resolved)
        return ids
```

---

## 5. In-Memory Query Execution & Pagination

Use `RqlEngine.create_in_memory(...)` or `InMemoryRqlExecutor` to filter and sort Python lists, dataclasses, or Pydantic models in memory.

```python
from dataclasses import dataclass, field
from datetime import datetime, timezone
from rql import (
    DynamicEntityFieldAccessor,
    FieldMetadataBuilder,
    InMemoryRqlExecutor,
    InMemoryRqlSearchService,
    RqlEngine,
)


@dataclass
class Assignee:
    user_id: int
    username: str


@dataclass
class Issue:
    id: int
    ProjectKey: str
    StatusId: int
    StatusName: str
    Summary: str
    Description: str | None
    Votes: int
    Created: datetime
    Assignees: list[Assignee] = field(default_factory=list)


# 1. Build field metadata
builder: FieldMetadataBuilder[Issue] = FieldMetadataBuilder()
registry = (
    builder.add_simple_field("id", lambda i: i.id)
    .add_simple_field(lambda i: i.ProjectKey, aliases=["project"])
    .add_simple_field("summary", lambda i: i.Summary)
    .add_simple_field("description", lambda i: i.Description)
    .add_simple_field("votes", lambda i: i.Votes)
    .add_simple_field("created", lambda i: i.Created)
    .add_lookup_field(
        scalar_expression=lambda i: i.StatusName,
        fk_expression=lambda i: i.StatusId,
    )
    .add_collection_field(
        scalar_expression=lambda i: i.Assignees,
        collection_contains_builder=lambda val: (
            lambda i: any(a.username.lower() == val.lower() for a in i.Assignees)
        ),
        collection_contains_substring_builder=lambda val: (
            lambda i: any(val.lower() in a.username.lower() for a in i.Assignees)
        ),
        collection_is_empty_expression=lambda i: len(i.Assignees) == 0,
        collection_contains_by_id_builder=lambda uid: (
            lambda i: any(a.user_id == uid for a in i.Assignees)
        ),
        collection_contains_by_ids_builder=lambda uids: (
            lambda i: any(a.user_id in uids for a in i.Assignees)
        ),
    )
    .add_computed_field("text", lambda i: f"{i.Summary} {i.Description or ''}")
    .build()
)

accessor = DynamicEntityFieldAccessor(registry)
lookup_resolver = IssueLookupResolver()

# 2. Execute queries directly via RqlEngine
engine = RqlEngine.create_in_memory(
    field_accessors=[accessor],
    collection_accessor=accessor,
    lookup_resolver=lookup_resolver,
    lookup_field_accessor=accessor,
)

issues = [
    Issue(
        id=1,
        ProjectKey="CRM",
        StatusId=1,
        StatusName="Open",
        Summary="OAuth login failure",
        Description="Refresh token rejected",
        Votes=15,
        Created=datetime.now(timezone.utc),
        Assignees=[Assignee(user_id=101, username="alice")],
    ),
]

matched = engine.execute(
    issues,
    'project = "CRM" AND status = "Open" AND assignee = "alice" AND created >= startOfDay() ORDER BY votes DESC',
)
print("Matched IDs:", [i.id for i in matched])

# 3. Paginated search via InMemoryRqlSearchService
executor = InMemoryRqlExecutor(
    field_accessors=[accessor],
    function_resolvers=[],
    collection_accessor=accessor,
    lookup_resolver=lookup_resolver,
    lookup_field_accessor=accessor,
)
search_service = InMemoryRqlSearchService(
    source_provider=lambda: issues,
    executor=executor,
    mapper=lambda issue: {"id": issue.id, "summary": issue.Summary},
)

page = search_service.search('project = "CRM"', skip=0, take=20)
print(f"Total: {page.total}, Pages: {page.total_pages}, Items: {page.items}")
```

---

## 6. SQLAlchemy 2.0 Query Execution & Pagination

`SqlAlchemyRqlExecutor` translates an `RqlQuery` directly into SQLAlchemy `WHERE` and `ORDER BY` clauses on a `Select` statement so filtering, sorting, and pagination happen entirely in SQL.

```python
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship

from rql import (
    BuiltInRqlFunctionResolver,
    DynamicEntityFieldAccessor,
    FieldMetadataBuilder,
    RqlParser,
    SqlAlchemyRqlSearchService,
)
from rql.backends.sqlalchemy import SqlAlchemyRqlExecutor


class Base(DeclarativeBase):
    pass


class IssueAssigneeModel(Base):
    __tablename__ = "issue_assignees"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    issue_id: Mapped[int] = mapped_column(ForeignKey("issues.id"))
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    username: Mapped[str] = mapped_column(String(100))


class IssueModel(Base):
    __tablename__ = "issues"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project: Mapped[str] = mapped_column(String(50), index=True)
    status_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    status_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    summary: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    votes: Mapped[int] = mapped_column(Integer, default=0)
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    assignees: Mapped[list[IssueAssigneeModel]] = relationship(IssueAssigneeModel)


# 1. Register SQLAlchemy model attributes in FieldMetadataBuilder
builder: FieldMetadataBuilder[IssueModel] = FieldMetadataBuilder()
sql_registry = (
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
        func.coalesce(IssueModel.summary, "") + " " + func.coalesce(IssueModel.description, ""),
    )
    .build()
)

sql_accessor = DynamicEntityFieldAccessor(sql_registry)
sql_executor = SqlAlchemyRqlExecutor(
    field_accessors=[sql_accessor],
    function_resolvers=[BuiltInRqlFunctionResolver()],
    collection_accessor=sql_accessor,
    lookup_resolver=IssueLookupResolver(),
    lookup_field_accessor=sql_accessor,
)


# 2. Apply RQL to a SQLAlchemy Select statement
def build_issue_select(rql: str):
    query = RqlParser.parse(rql)
    stmt = select(IssueModel)
    return sql_executor.execute(stmt, query)


# 3. Execute paginated search with SqlAlchemyRqlSearchService
def search_issues(session: Session, rql: str, skip: int = 0, take: int = 25):
    service = SqlAlchemyRqlSearchService(
        session_factory=lambda: session,
        base_select_provider=lambda: select(IssueModel),
        executor=sql_executor,
        mapper=lambda row: {"id": row.id, "project": row.project, "summary": row.summary},
    )
    return service.search(rql, skip=skip, take=take)
```

---

## 7. Customizing Functions & Operators

### Adding Custom RQL Functions (`IRqlFunctionResolver`)
Implement `IRqlFunctionResolver` to resolve custom RQL functions such as `currentUser()` or `openSprints()`:

```python
from collections.abc import Sequence
from rql import BuiltInRqlFunctionResolver, IRqlFunctionResolver


class CurrentUserFunctionResolver(IRqlFunctionResolver[object]):
    def __init__(self, current_username: str) -> None:
        self._username = current_username

    def handles(self, function_name: str) -> bool:
        return function_name.lower() == "currentuser"

    def resolve(
        self,
        function_name: str,
        args: Sequence[str],
        context_entity: object | None = None,
    ) -> str:
        return self._username


# Pass your custom resolver ahead of BuiltInRqlFunctionResolver:
resolvers = [CurrentUserFunctionResolver("alice"), BuiltInRqlFunctionResolver()]
```

### Registering Custom In-Memory Operators (`ScalarOperatorRegistry`)
```python
from rql import ScalarOperatorRegistry

registry = ScalarOperatorRegistry()
registry.register(
    "startswith",
    lambda field_val, vals, first, is_null: (
        field_val is not None and str(field_val).lower().startswith(first.lower())
    ),
)
```

---

## 8. API Reference Summary

| Class / Function | Module | Description |
|---|---|---|
| `RqlLexer` | `rql.lexer` | Tokenizes an RQL string into a list of `Token` objects. |
| `RqlParser` | `rql.parser` | Parses RQL strings or tokens into an immutable `RqlQuery` AST. |
| `RqlNormalizer` | `rql.services` | Serializes an `RqlQuery` AST into a canonical RQL string. |
| `RqlValidationService` | `rql.services` | Validates RQL syntax and returns `RqlValidationResult`. |
| `RqlMetadata` | `rql.metadata` | Holds schema definitions (`fields`, `operators`, `functions`). |
| `RqlMetadataService` | `rql.services` | Projects `RqlMetadata` into an `RqlMetadataResponse` DTO. |
| `RqlAutocompleteService` | `rql.services` | Returns prefix-based field and value suggestions. |
| `FieldMetadataBuilder` | `rql.metadata` | Registers simple, lookup, collection, and computed entity fields. |
| `FieldMetadataRegistry` | `rql.metadata` | Stores canonical field metadata and resolves field aliases. |
| `DynamicEntityFieldAccessor` | `rql.metadata` | Provides field, lookup, and collection access from a `FieldMetadataRegistry`. |
| `BuiltInRqlFunctionResolver` | `rql.functions` | Resolves built-in date and user functions (`now()`, `startOfDay()`, etc.). |
| `InMemoryRqlExecutor` | `rql.backends.in_memory` | Filters and sorts in-memory `Iterable[T]` collections. |
| `SqlAlchemyRqlExecutor` | `rql.backends.sqlalchemy` | Applies RQL `WHERE` and `ORDER BY` clauses to a SQLAlchemy `Select`. |
| `InMemoryRqlSearchService` | `rql.services` | Executes paginated RQL searches (`PagedResult`) over in-memory iterables. |
| `SqlAlchemyRqlSearchService` | `rql.services` | Executes paginated RQL searches (`PagedResult`) over a SQLAlchemy `Session`. |
| `RqlEngine` | `rql` | Unified entry point for parsing, normalizing, validating, autocompleting, and executing RQL. |
