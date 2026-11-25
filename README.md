# RQL (`rql`)

Python query engine for **RQL (Resource Query Language)**—a JQL-inspired query language for filtering, sorting, validating, and autocompleting structured records across in-memory Python collections and SQLAlchemy 2.0 ORM queries.

📘 **Full Usage Guide:** [docs/USAGE_GUIDE.md](docs/USAGE_GUIDE.md)

---

## Features

- **Complete RQL Grammar:** `AND`, `OR`, `NOT`, parentheses, `=`, `!=`, `<`, `<=`, `>`, `>=`, `~`, `!~`, `IN`, `NOT IN`, `IS EMPTY`, `IS NOT NULL`, `WAS`, `WAS IN`, `WAS NOT`, `WAS NOT IN`, `CHANGED`, function calls (`now()`, `startOfDay("-1")`, `membersOf("devs")`), and multi-column `ORDER BY`.
- **In-Memory & SQLAlchemy 2.0 Execution:**
  - **In-Memory (`InMemoryRqlExecutor`):** Zero-dependency filtering, sorting, and pagination over Python dataclasses, Pydantic models, or plain objects.
  - **SQLAlchemy 2.0 (`SqlAlchemyRqlExecutor`):** Translates RQL queries directly into SQLAlchemy `Select` statements with foreign-key lookup optimization (`status = "Open"` $\rightarrow$ `issues.status_id = 1` without table joins) and `.any()` collection predicates.
- **Dynamic Field Metadata (`FieldMetadataBuilder` & `DynamicEntityFieldAccessor`):** Register simple, lookup, collection, and computed fields with automatic property name extraction, `camelCase` conversion, `Id` suffix stripping, plural singularization (`Assignees` $\rightarrow$ `assignee`), and field aliases.
- **Built-In Query Services:** Canonical query normalization (`RqlNormalizer`), syntax validation (`RqlValidationService`), schema inspection (`RqlMetadataService`), and prefix-based autocomplete (`RqlAutocompleteService`).
- **Fully Typed:** Passes `mypy --strict` with zero errors.

---

## Installation

```bash
# Core package (zero runtime dependencies)
pip install -e .

# With SQLAlchemy 2.0 support & development tools
pip install -e ".[sqlalchemy,dev]"
```

---

## Quick Start

### 1. Parse, Validate, Normalize & Autocomplete

```python
from rql import (
    RqlAutocompleteService,
    RqlMetadata,
    RqlNormalizer,
    RqlParser,
    RqlValidationService,
)

normalizer = RqlNormalizer()
validator = RqlValidationService(normalizer)

res = validator.validate("Project = 'CRM' and Status in ('Open', 'In Progress') order by created desc")
print(res.valid)           # True
print(res.normalized_rql)  # (project = "CRM" AND status IN ("Open", "In Progress")) ORDER BY created DESC

autocomplete = RqlAutocompleteService(RqlMetadata())
print(autocomplete.get_suggestions(field="priority", query="hi").suggestions)  # ['High']
```

### 2. Filter & Sort Records (`RqlEngine`)

```python
from dataclasses import dataclass
from datetime import datetime, timezone
from rql import DynamicEntityFieldAccessor, FieldMetadataBuilder, ILookupResolver, RqlEngine


@dataclass
class Issue:
    id: int
    project: str
    status_id: int
    status_name: str
    summary: str
    votes: int
    created: datetime


class StatusLookupResolver(ILookupResolver):
    def is_lookup_field(self, field_name: str) -> bool:
        return field_name.lower() == "status"

    def resolve(self, field_name: str, display_value: str) -> int | None:
        return {"open": 1, "closed": 2}.get(display_value.lower())

    def resolve_many(self, field_name: str, display_values):
        return [r for v in display_values if (r := self.resolve(field_name, v)) is not None]


registry = (
    FieldMetadataBuilder[Issue]()
    .add_simple_field("id", lambda i: i.id)
    .add_simple_field("project", lambda i: i.project)
    .add_simple_field("summary", lambda i: i.summary)
    .add_simple_field("votes", lambda i: i.votes)
    .add_simple_field("created", lambda i: i.created)
    .add_lookup_field("status", lambda i: i.status_name, lambda i: i.status_id)
    .build()
)
accessor = DynamicEntityFieldAccessor(registry)

engine = RqlEngine.create_in_memory(
    field_accessors=[accessor],
    collection_accessor=accessor,
    lookup_resolver=StatusLookupResolver(),
    lookup_field_accessor=accessor,
)

issues = [
    Issue(1, "CRM", 1, "Open", "Login bug", 10, datetime.now(timezone.utc)),
    Issue(2, "CRM", 2, "Closed", "Old task", 2, datetime.now(timezone.utc)),
]

matched = engine.execute(issues, 'project = "CRM" AND status = "Open" AND votes >= 5')
```

See [docs/USAGE_GUIDE.md](docs/USAGE_GUIDE.md) for complete examples including collection fields, computed fields, SQLAlchemy 2.0 integration, pagination (`PagedResult`), and custom functions.

---

## Running Tests & Type Checks

```bash
pytest -v
mypy --strict src tests
```
