"""RQL Schema and Dynamic Field Metadata package."""

from rql.metadata.builder import FieldMetadataBuilder
from rql.metadata.dynamic_accessor import DynamicEntityFieldAccessor
from rql.metadata.field_metadata import (
    CollectionFieldMetadata,
    ComputedFieldMetadata,
    FieldMetadata,
    LookupFieldMetadata,
    SimpleFieldMetadata,
)
from rql.metadata.registry import FieldMetadataRegistry
from rql.metadata.schema import RqlField, RqlFunction, RqlMetadata

__all__ = [
    "CollectionFieldMetadata",
    "ComputedFieldMetadata",
    "DynamicEntityFieldAccessor",
    "FieldMetadata",
    "FieldMetadataBuilder",
    "FieldMetadataRegistry",
    "LookupFieldMetadata",
    "RqlField",
    "RqlFunction",
    "RqlMetadata",
    "SimpleFieldMetadata",
]
