"""Segregated field accessor and lookup resolver protocols group."""

from rql.abstractions.accessors.collection_field_accessor import ICollectionFieldAccessor
from rql.abstractions.accessors.entity_field_accessor import IEntityFieldAccessor
from rql.abstractions.accessors.lookup_field_accessor import ILookupFieldAccessor
from rql.abstractions.accessors.lookup_resolver import ILookupResolver

__all__ = [
    "ICollectionFieldAccessor",
    "IEntityFieldAccessor",
    "ILookupFieldAccessor",
    "ILookupResolver",
]
