"""RQL Metadata Service projecting RqlMetadata to RqlMetadataResponse (SRP)."""

from __future__ import annotations

from rql.abstractions.services import IRqlMetadataService
from rql.metadata.schema import RqlMetadata
from rql.models.dtos import RqlFieldMeta, RqlFunctionMeta, RqlMetadataResponse

_DEFAULT_KEYWORDS: list[str] = [
    "AND",
    "OR",
    "NOT",
    "IN",
    "IS",
    "WAS",
    "CHANGED",
    "ORDER BY",
    "ASC",
    "DESC",
    "EMPTY",
    "NULL",
]


class RqlMetadataService(IRqlMetadataService):
    """Provides read-only RQL schema metadata for consumers."""

    def __init__(self, meta: RqlMetadata) -> None:
        self._meta = meta

    def get_metadata(self) -> RqlMetadataResponse:
        return RqlMetadataResponse(
            fields=[
                RqlFieldMeta(f.name, f.type, list(f.allowed_values))
                for f in self._meta.fields
            ],
            operators=list(self._meta.operators),
            functions=[
                RqlFunctionMeta(fn.name, fn.return_type, fn.description)
                for fn in self._meta.functions
            ],
            keywords=list(_DEFAULT_KEYWORDS),
        )
