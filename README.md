# rql-python — JQL-Inspired Query Language & Dynamic Filter Engine for Python and SQLAlchemy 2.0

[![CI](https://github.com/altunga/rql-python/actions/workflows/ci.yml/badge.svg)](https://github.com/altunga/rql-python/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![SQLAlchemy 2.0](https://img.shields.io/badge/SQLAlchemy-2.0-red.svg)](https://www.sqlalchemy.org/)
[![Typed: mypy strict](https://img.shields.io/badge/typed-mypy%20strict-brightgreen.svg)](https://mypy-lang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**`rql-python`** is a fast, strictly typed **Python query language parser and dynamic query engine** inspired by **Jira Query Language (JQL)**. Write human-friendly search queries—complete with boolean logic, comparison operators, date functions, `IN`/`IS EMPTY` filters, and `ORDER BY`—and execute them directly against **SQLAlchemy 2.0** databases or **in-memory Python collections** (dataclasses, Pydantic models, plain objects).

```sql
project = "CRM" AND status IN ("Open", "In Progress") AND assignee = currentUser() AND created >= startOfDay("-7") ORDER BY priority ASC, votes DESC
```

📘 **[Read the Full Developer Usage Guide](docs/USAGE_GUIDE.md)** | 🚀 **[Explore the Runnable Showcase (`samples/main.py`)](samples/main.py)**

---

## Why Use `rql-python`?

Building advanced search bars, REST API dynamic filtering (FastAPI / Flask / Django), or Jira-like issue filters usually requires writing brittle string parsers or exposing unsafe raw SQL. `rql-python` gives you a complete, safe, extensible search stack out of the box:

- **Zero-Dependency Core:** Lexer, parser, AST, normalizer, validator, autocomplete, and in-memory execution require **no third-party runtime packages**.
- **Native SQLAlchemy 2.0 Query Compilation:** Translates RQL directly into parameterized SQLAlchemy `Select` statements—avoiding SQL injection and eliminating unnecessary table joins via integer foreign-key lookup resolution (`status = "Open"` -> `issues.status_id = 1`).
- **Frontend-Ready Services:** Includes syntax validation (`RqlValidationService`), canonical formatting (`RqlNormalizer`), schema inspection (`RqlMetadataService`), and prefix-based autocomplete (`RqlAutocompleteService`) for building interactive search inputs.
- **Full JQL-Style Grammar:** Supports `AND`, `OR`, `NOT`, parentheses `(...)`, `=`, `!=`, `<`, `<=`, `>`, `>=`, `~` (contains), `!~`, `IN`, `NOT IN`, `IS EMPTY`, `IS NOT NULL`, `WAS`, `WAS IN`, `WAS NOT`, `WAS NOT IN`, `CHANGED`, built-in & custom functions (`now()`, `startOfDay("-1")`, `membersOf("team")`, `currentUser()`), and multi-column `ORDER BY`.
- **100% Strictly Typed (PEP 561):** Ships with `py.typed` and passes `mypy --strict` with zero errors.

---

## Installation

```bash
# Core package (zero runtime dependencies — in-memory execution, parser, validator, autocomplete)
pip install git+https://github.com/altunga/rql-python.git

# With SQLAlchemy 2.0 support
pip install "rql-python[sqlalchemy] @ git+https://github.com/altunga/rql-python.git"

# Local development install
git clone https://github.com/altunga/rql-python.git
cd rql-python
pip install -e ".[sqlalchemy,dev]"
```

---

## Quick Start

### 1. Parse, Validate, Normalize & Autocomplete

```python
from rql import (
    RqlAutocompleteService,
    RqlField,
    RqlMetadata,
    RqlNormalizer,
    RqlValidationService,
)

normalizer = RqlNormalizer()
validator = RqlValidationService(normalizer)

res = validator.validate("Project = 'CRM' and Status in ('Open', 'In Progress') order by created desc")
print(res.valid)           # True
print(res.normalized_rql)  # (project = "CRM" AND status IN ("Open", "In Progress")) ORDER BY created DESC

metadata = RqlMetadata(
    fields=[
        RqlField("project", "text", ["CRM", "SUP", "DEV"]),
        RqlField("priority", "text", ["Critical", "High", "Medium", "Low"]),
        RqlField("created", "date", []),
    ]
)
autocomplete = RqlAutocompleteService(metadata)
print(autocomplete.get_suggestions(field="priority", query="hi").suggestions)  # ['High']
print(autocomplete.get_suggestions(field="created", query="startOf").suggestions)
# ['startOfDay()', 'startOfWeek()', 'startOfMonth()', 'startOfYear()']
```

### 2. Dynamic Filtering on In-Memory Python Objects (`RqlEngine`)

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

### 3. Dynamic SQL Queries with SQLAlchemy 2.0

```python
from sqlalchemy import select
from rql import BuiltInRqlFunctionResolver, RqlParser
from rql.backends.sqlalchemy import SqlAlchemyRqlExecutor

executor = SqlAlchemyRqlExecutor(
    field_accessors=[sql_accessor],
    function_resolvers=[BuiltInRqlFunctionResolver()],
    collection_accessor=sql_accessor,
    lookup_resolver=lookup_resolver,
    lookup_field_accessor=sql_accessor,
)

stmt = executor.execute(
    select(IssueModel),
    RqlParser.parse('project = "CRM" AND status = "Open" ORDER BY votes DESC'),
)
rows = session.scalars(stmt).all()
```

See **[docs/USAGE_GUIDE.md](docs/USAGE_GUIDE.md)** and **[samples/main.py](samples/main.py)** for complete runnable examples covering collection fields, computed fields, custom functions, custom target compilers, and pagination (`PagedResult`).

---

## Running Samples, Tests & Type Checks

```bash
# Run the complete end-to-end sample application
python -m samples.main

# Run unit and integration test suite
pytest -v

# Run strict static type checking
mypy --strict src tests samples
```

---

## Contributing & License

Contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
Released under the [MIT License](LICENSE).
