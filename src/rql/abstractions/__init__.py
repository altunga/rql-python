"""Segregated protocols (ISP & DIP) for RQL field accessors, function resolvers, and services."""

from rql.abstractions.accessors import (
    ICollectionFieldAccessor,
    IEntityFieldAccessor,
    ILookupFieldAccessor,
    ILookupResolver,
)
from rql.abstractions.functions import IRqlFunctionResolver
from rql.abstractions.services import (
    IRqlAutocompleteService,
    IRqlExecutor,
    IRqlMetadataService,
    IRqlNormalizer,
    IRqlSearchService,
    IRqlValidationService,
)

__all__ = [
    "ICollectionFieldAccessor",
    "IEntityFieldAccessor",
    "ILookupFieldAccessor",
    "ILookupResolver",
    "IRqlAutocompleteService",
    "IRqlExecutor",
    "IRqlFunctionResolver",
    "IRqlMetadataService",
    "IRqlNormalizer",
    "IRqlSearchService",
    "IRqlValidationService",
]
