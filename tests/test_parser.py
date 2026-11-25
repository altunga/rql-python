"""Unit tests for RqlParser, AST nodes, and Visitor dispatch."""

from __future__ import annotations

import pytest

from rql.ast.nodes import (
    AndNode,
    FieldConditionNode,
    NotNode,
    OrderByClause,
    OrNode,
    RqlQuery,
    SortField,
)
from rql.exceptions import RqlParseException
from rql.parser.rql_parser import RqlParser


def test_parse_empty_query() -> None:
    query = RqlParser.parse("")
    assert query == RqlQuery(where=None, order_by=None)


def test_parse_simple_field_condition_lowercases_field_name() -> None:
    query = RqlParser.parse('Project = "CRM"')
    assert query.where == FieldConditionNode(
        field="project",
        operator="=",
        values=("CRM",),
    )
    assert query.order_by is None


def test_parse_operator_precedence_and_parentheses() -> None:
    # OR has lower precedence than AND; NOT has highest precedence
    query = RqlParser.parse('a = 1 OR NOT b = 2 AND c = 3')
    assert isinstance(query.where, OrNode)
    assert isinstance(query.where.left, FieldConditionNode)
    assert isinstance(query.where.right, AndNode)
    assert isinstance(query.where.right.left, NotNode)

    # Parentheses override precedence
    grouped = RqlParser.parse('(a = 1 OR b = 2) AND c = 3')
    assert isinstance(grouped.where, AndNode)
    assert isinstance(grouped.where.left, OrNode)


@pytest.mark.parametrize(
    ("rql", "expected_op", "expected_values"),
    [
        ('status != "Closed"', "!=", ("Closed",)),
        ("votes < 10", "<", ("10",)),
        ("votes <= 10", "<=", ("10",)),
        ("votes > 5", ">", ("5",)),
        ("votes >= 5", ">=", ("5",)),
        ('summary ~ "bug"', "~", ("bug",)),
        ('summary !~ "wip"', "!~", ("wip",)),
        ('status IN ("Open", "In Progress")', "in", ("Open", "In Progress")),
        ('status NOT IN ("Closed", "Resolved")', "not in", ("Closed", "Resolved")),
        ("assignee IS EMPTY", "is", ("EMPTY",)),
        ("assignee IS NOT NULL", "is not", ("NULL",)),
        ('status WAS "Open"', "was", ("Open",)),
        ('status WAS IN ("Open", "Reopened")', "was in", ("Open", "Reopened")),
        ('status WAS NOT "Closed"', "was not", ("Closed",)),
        ('status WAS NOT IN ("Closed")', "was not in", ("Closed",)),
        ("status CHANGED", "changed", ()),
    ],
)
def test_parse_all_operators(
    rql: str,
    expected_op: str,
    expected_values: tuple[str, ...],
) -> None:
    query = RqlParser.parse(rql)
    assert isinstance(query.where, FieldConditionNode)
    assert query.where.operator == expected_op
    assert query.where.values == expected_values


def test_parse_function_calls_with_and_without_arguments() -> None:
    q1 = RqlParser.parse("created >= now()")
    assert isinstance(q1.where, FieldConditionNode)
    assert q1.where.values == ("__fn:now()",)

    q2 = RqlParser.parse('created >= startOfDay("-1")')
    assert isinstance(q2.where, FieldConditionNode)
    assert q2.where.values == ("__fn:startOfDay(-1)",)

    q3 = RqlParser.parse('issue IN (linkedIssues("CRM-1", "blocks"))')
    assert isinstance(q3.where, FieldConditionNode)
    assert q3.where.values == ("__fn:linkedIssues(CRM-1,blocks)",)


def test_parse_order_by_clause_with_and_without_where() -> None:
    q1 = RqlParser.parse('project = "CRM" ORDER BY Created DESC, Priority ASC, Id')
    assert isinstance(q1.where, FieldConditionNode)
    assert q1.order_by == OrderByClause(
        fields=(
            SortField(field="created", asc=False),
            SortField(field="priority", asc=True),
            SortField(field="id", asc=True),
        )
    )

    q2 = RqlParser.parse("ORDER BY updated DESC")
    assert q2.where is None
    assert q2.order_by == OrderByClause(fields=(SortField(field="updated", asc=False),))


@pytest.mark.parametrize(
    "invalid_rql",
    [
        "status",
        "status =",
        "= 'Open'",
        "status IN 'Open'",
        "(status = 'Open'",
        "status = 'Open' trailing_unexpected",
        "ORDER",
    ],
)
def test_parse_invalid_syntax_raises_rql_parse_exception(invalid_rql: str) -> None:
    with pytest.raises(RqlParseException):
        RqlParser.parse(invalid_rql)
