"""RqlEngine Facade providing a unified entry point to the RQL subsystem (GoF Facade pattern)."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Generic, TypeVar

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
    IRqlValidationService,
)
from rql.ast.nodes import RqlQuery
from rql.backends.in_memory.executor import InMemoryRqlExecutor
from rql.functions.builtin_resolver import BuiltInRqlFunctionResolver
from rql.metadata.schema import RqlMetadata
from rql.models.dtos import (
    RqlAutocompleteResponse,
    RqlMetadataResponse,
    RqlValidationResult,
)
from rql.parser.rql_parser import RqlParser
from rql.services.autocomplete_service import RqlAutocompleteService
from rql.services.metadata_service import RqlMetadataService
from rql.services.normalizer import RqlNormalizer
from rql.services.validation_service import RqlValidationService

T = TypeVar("T")
TQuery = TypeVar("TQuery")


class RqlEngine(Generic[T, TQuery]):
    """GoF Facade simplifying access to parsing, normalization, validation, metadata, and execution."""

    def __init__(
        self,
        executor: IRqlExecutor[T, TQuery],
        normalizer: IRqlNormalizer | None = None,
        validation_service: IRqlValidationService | None = None,
        metadata_service: IRqlMetadataService | None = None,
        autocomplete_service: IRqlAutocompleteService | None = None,
        metadata: RqlMetadata | None = None,
    ) -> None:
        meta = metadata or RqlMetadata()
        norm = normalizer or RqlNormalizer()
        self._executor = executor
        self._normalizer = norm
        self._validation_service = validation_service or RqlValidationService(norm)
        self._metadata_service = metadata_service or RqlMetadataService(meta)
        self._autocomplete_service = autocomplete_service or RqlAutocompleteService(meta)

    @staticmethod
    def create_in_memory(
        field_accessors: Iterable[IEntityFieldAccessor[T]],
        collection_accessor: ICollectionFieldAccessor[T],
        lookup_resolver: ILookupResolver,
        lookup_field_accessor: ILookupFieldAccessor[T],
        function_resolvers: Iterable[IRqlFunctionResolver[T]] | None = None,
        metadata: RqlMetadata | None = None,
    ) -> RqlEngine[T, list[T]]:
        """Factory method creating an RqlEngine configured with InMemoryRqlExecutor."""
        resolvers = (
            list(function_resolvers)
            if function_resolvers is not None
            else [BuiltInRqlFunctionResolver()]
        )
        executor: InMemoryRqlExecutor[T] = InMemoryRqlExecutor(
            field_accessors=field_accessors,
            function_resolvers=resolvers,
            collection_accessor=collection_accessor,
            lookup_resolver=lookup_resolver,
            lookup_field_accessor=lookup_field_accessor,
        )
        return RqlEngine(executor=executor, metadata=metadata)

    def parse(self, rql: str) -> RqlQuery:
        """Parses an RQL string into an RqlQuery AST."""
        return RqlParser.parse(rql)

    def normalize(self, rql_or_query: str | RqlQuery) -> str:
        """Normalizes an RQL string or RqlQuery AST to its canonical string form."""
        query = (
            RqlParser.parse(rql_or_query)
            if isinstance(rql_or_query, str)
            else rql_or_query
        )
        return self._normalizer.normalize(query)

    def validate(self, rql: str | None) -> RqlValidationResult:
        """Validates an RQL string and returns RqlValidationResult."""
        return self._validation_service.validate(rql)

    def get_metadata(self) -> RqlMetadataResponse:
        """Returns schema metadata (fields, operators, functions, keywords)."""
        return self._metadata_service.get_metadata()

    def get_suggestions(
        self, field: str | None = None, query: str | None = None
    ) -> RqlAutocompleteResponse:
        """Returns autocomplete suggestions for field names or values."""
        return self._autocomplete_service.get_suggestions(field, query)

    def execute(self, source: TQuery, rql_or_query: str | RqlQuery) -> TQuery:
        """Executes an RQL string or RqlQuery against source."""
        query = (
            RqlParser.parse(rql_or_query)
            if isinstance(rql_or_query, str)
            else rql_or_query
        )
        return self._executor.execute(source, query)
