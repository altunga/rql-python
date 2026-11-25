"""Unit tests for FieldMetadataBuilder, FieldMetadataRegistry, and DynamicEntityFieldAccessor."""

from __future__ import annotations

from dataclasses import dataclass, field
import pytest

from rql.metadata.builder import FieldMetadataBuilder
from rql.metadata.dynamic_accessor import DynamicEntityFieldAccessor


@dataclass
class AssigneeItem:
    user_id: int
    username: str


@dataclass
class IssueEntity:
    Id: int
    ProjectKey: str
    StatusId: int
    StatusName: str
    Summary: str
    Description: str
    Assignees: list[AssigneeItem] = field(default_factory=list)
    Categories: list[str] = field(default_factory=list)
    Addresses: list[str] = field(default_factory=list)


def test_builder_automatic_name_extraction_and_singularization() -> None:
    builder: FieldMetadataBuilder[IssueEntity] = FieldMetadataBuilder()
    registry = (
        builder.add_simple_field(lambda i: i.ProjectKey, aliases=["project"])
        .add_lookup_field(
            scalar_expression=lambda i: i.StatusName,
            fk_expression=lambda i: i.StatusId,
        )
        .add_collection_field(
            scalar_expression=lambda i: i.Assignees,
            collection_contains_builder=lambda val: (
                lambda i: any(a.username.lower() == val.lower() for a in i.Assignees)
            ),
            collection_contains_substring_builder=lambda val: (
                lambda i: any(val.lower() in a.username.lower() for a in i.Assignees)
            ),
            collection_is_empty_expression=lambda i: len(i.Assignees) == 0,
            collection_contains_by_id_builder=lambda uid: (
                lambda i: any(a.user_id == uid for a in i.Assignees)
            ),
            collection_contains_by_ids_builder=lambda uids: (
                lambda i: any(a.user_id in uids for a in i.Assignees)
            ),
        )
        .add_collection_field(
            scalar_expression=lambda i: i.Categories,
            collection_contains_builder=lambda val: (lambda i: val in i.Categories),
            collection_contains_substring_builder=lambda val: (
                lambda i: any(val in c for c in i.Categories)
            ),
            collection_is_empty_expression=lambda i: len(i.Categories) == 0,
        )
        .add_collection_field(
            scalar_expression=lambda i: i.Addresses,
            collection_contains_builder=lambda val: (lambda i: val in i.Addresses),
            collection_contains_substring_builder=lambda val: (
                lambda i: any(val in a for a in i.Addresses)
            ),
            collection_is_empty_expression=lambda i: len(i.Addresses) == 0,
        )
        .add_computed_field("text", lambda i: f"{i.Summary} {i.Description}")
        .add_alias("projectKey", "proj")
        .build()
    )

    names = set(registry.get_field_names())
    assert names == {"projectkey", "status", "assignee", "category", "address", "text"}

    # Alias lookup works for both inline aliases and add_alias()
    assert registry.get_field("project") is not None
    assert registry.get_field("proj") is not None
    assert registry.get_field("PROJECTKEY") is not None
    assert registry.get_field("nonexistent") is None


def test_dynamic_entity_field_accessor_delegation() -> None:
    builder: FieldMetadataBuilder[IssueEntity] = FieldMetadataBuilder()
    registry = (
        builder.add_simple_field("project", lambda i: i.ProjectKey)
        .add_lookup_field("status", lambda i: i.StatusName, lambda i: i.StatusId)
        .add_collection_field(
            "assignee",
            scalar_expression=lambda i: i.Assignees,
            collection_contains_builder=lambda val: (
                lambda i: any(a.username.lower() == val.lower() for a in i.Assignees)
            ),
            collection_contains_substring_builder=lambda val: (
                lambda i: any(val.lower() in a.username.lower() for a in i.Assignees)
            ),
            collection_is_empty_expression=lambda i: len(i.Assignees) == 0,
            collection_contains_by_id_builder=lambda uid: (
                lambda i: any(a.user_id == uid for a in i.Assignees)
            ),
            collection_contains_by_ids_builder=lambda uids: (
                lambda i: any(a.user_id in uids for a in i.Assignees)
            ),
        )
        .add_computed_field("text", lambda i: f"{i.Summary} {i.Description}")
        .build()
    )

    accessor = DynamicEntityFieldAccessor(registry)
    issue = IssueEntity(
        Id=1,
        ProjectKey="CRM",
        StatusId=2,
        StatusName="Open",
        Summary="Login bug",
        Description="OAuth fails",
        Assignees=[AssigneeItem(user_id=10, username="alice")],
    )

    assert accessor.handles("project") is True
    assert accessor.handles("unknown") is False
    assert accessor.get_value(issue, "project") == "CRM"
    assert accessor.get_value(issue, "text") == "Login bug OAuth fails"
    assert accessor.get_value(issue, "unknown") is None

    assert accessor.is_lookup_field("status") is True
    assert accessor.is_lookup_field("project") is False
    fk_expr = accessor.get_fk_expression("status")
    assert fk_expr(issue) == 2

    assert accessor.is_collection_field("assignee") is True
    assert accessor.is_collection_field("project") is False
    assert accessor.is_collection_field("unknown") is False
    assert accessor.get_collection_contains_expression("assignee", "ALICE")(issue) is True
    assert accessor.get_collection_contains_substring_expression("assignee", "lic")(issue) is True
    assert accessor.get_collection_is_empty_expression("assignee")(issue) is False

    by_id = accessor.get_collection_contains_by_id_expression("assignee", 10)
    assert by_id is not None and by_id(issue) is True
    by_ids = accessor.get_collection_contains_by_ids_expression("assignee", [99, 10])
    assert by_ids is not None and by_ids(issue) is True


def test_builder_validation_errors() -> None:
    builder: FieldMetadataBuilder[IssueEntity] = FieldMetadataBuilder()
    with pytest.raises(ValueError, match="No fields registered"):
        builder.build()

    with pytest.raises(ValueError, match="Canonical field 'missing' not registered"):
        builder.add_alias("missing", "m")


def test_builder_positional_collection_field_and_snake_case_alias() -> None:
    builder: FieldMetadataBuilder[IssueEntity] = FieldMetadataBuilder()
    registry = builder.add_collection_field(
        lambda i: i.Assignees,
        lambda val: (lambda i: any(a.username.lower() == val.lower() for a in i.Assignees)),
        lambda val: (lambda i: any(val.lower() in a.username.lower() for a in i.Assignees)),
        lambda i: len(i.Assignees) == 0,
    ).build()
    assert registry.get_field("assignee") is not None
