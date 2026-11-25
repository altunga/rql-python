"""Unit tests for RqlNormalizer (Visitor pattern) and RqlValidationService."""

from __future__ import annotations

from rql.parser.rql_parser import RqlParser
from rql.services.normalizer import RqlNormalizer
from rql.services.validation_service import RqlValidationService


def test_normalizer_empty_query() -> None:
    normalizer = RqlNormalizer()
    assert normalizer.normalize(RqlParser.parse("")) == ""


def test_normalizer_single_and_list_conditions() -> None:
    normalizer = RqlNormalizer()
    assert normalizer.normalize(RqlParser.parse("status = 'Open'")) == 'status = "Open"'
    assert (
        normalizer.normalize(RqlParser.parse("status in ('Open', 'Closed')"))
        == 'status IN ("Open", "Closed")'
    )
    assert normalizer.normalize(RqlParser.parse("status changed")) == "status CHANGED"


def test_normalizer_single_item_list_operator_roundtrips() -> None:
    normalizer = RqlNormalizer()
    normalized = normalizer.normalize(RqlParser.parse('status IN ("Open")'))
    assert normalized == 'status IN ("Open")'
    # Must re-parse without error
    reparsed = RqlParser.parse(normalized)
    assert normalizer.normalize(reparsed) == 'status IN ("Open")'


def test_normalizer_boolean_tree_and_order_by() -> None:
    normalizer = RqlNormalizer()
    query = RqlParser.parse(
        "project = 'CRM' and (status = 'Open' or not priority = 'Low') order by created desc, id asc"
    )
    assert (
        normalizer.normalize(query)
        == '(project = "CRM" AND (status = "Open" OR NOT priority = "Low")) ORDER BY created DESC, id ASC'
    )


def test_validation_service_empty_and_whitespace() -> None:
    service = RqlValidationService(RqlNormalizer())
    for empty_val in (None, "", "   "):
        result = service.validate(empty_val)
        assert result.valid is True
        assert result.errors == []
        assert result.normalized_rql is None


def test_validation_service_valid_and_invalid_queries() -> None:
    service = RqlValidationService(RqlNormalizer())

    valid_res = service.validate("project = 'CRM' AND status != 'Closed'")
    assert valid_res.valid is True
    assert valid_res.errors == []
    assert valid_res.normalized_rql == '(project = "CRM" AND status != "Closed")'

    invalid_res = service.validate("project =")
    assert invalid_res.valid is False
    assert len(invalid_res.errors) == 1
    assert "Expected value" in invalid_res.errors[0]
