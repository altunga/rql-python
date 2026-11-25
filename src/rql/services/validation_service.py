"""RQL Validation Service (SRP & DIP)."""

from __future__ import annotations

from rql.abstractions.services import IRqlNormalizer, IRqlValidationService
from rql.exceptions import RqlParseException
from rql.models.dtos import RqlValidationResult
from rql.parser.rql_parser import RqlParser


class RqlValidationService(IRqlValidationService):
    """Validates an RQL string and returns normalized output or error messages."""

    def __init__(self, normalizer: IRqlNormalizer) -> None:
        self._normalizer = normalizer

    def validate(self, rql: str | None) -> RqlValidationResult:
        if rql is None or not rql.strip():
            return RqlValidationResult(valid=True)

        try:
            query = RqlParser.parse(rql)
            return RqlValidationResult(
                valid=True,
                normalized_rql=self._normalizer.normalize(query),
            )
        except RqlParseException as ex:
            return RqlValidationResult(
                valid=False,
                errors=[str(ex)],
            )
