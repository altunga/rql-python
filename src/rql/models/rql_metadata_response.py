"""Full RQL schema metadata response DTO."""

from __future__ import annotations

from dataclasses import dataclass, field

from rql.models.rql_field_meta import RqlFieldMeta
from rql.models.rql_function_meta import RqlFunctionMeta


@dataclass
class RqlMetadataResponse:
    """Full RQL schema metadata: fields, operators, functions, keywords."""

    fields: list[RqlFieldMeta] = field(default_factory=list)
    operators: list[str] = field(default_factory=list)
    functions: list[RqlFunctionMeta] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
