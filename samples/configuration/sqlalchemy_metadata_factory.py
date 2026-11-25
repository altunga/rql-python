"""Factory building FieldMetadataRegistry and DynamicEntityFieldAccessor for SQLAlchemy IssueModel."""

from __future__ import annotations

from sqlalchemy import func

from rql.metadata import DynamicEntityFieldAccessor, FieldMetadataBuilder
from samples.models.sqlalchemy.issue_assignee_model import IssueAssigneeModel
from samples.models.sqlalchemy.issue_model import IssueModel


def create_sqlalchemy_accessor() -> DynamicEntityFieldAccessor[IssueModel]:
    """Configures Simple, Lookup, Collection, and Computed fields for the SQLAlchemy IssueModel."""
    builder: FieldMetadataBuilder[IssueModel] = FieldMetadataBuilder()
    registry = (
        builder.add_simple_field("id", IssueModel.id)
        .add_simple_field("key", IssueModel.key)
        .add_simple_field("project", IssueModel.project)
        .add_simple_field("summary", IssueModel.summary)
        .add_simple_field("description", IssueModel.description)
        .add_simple_field("sprint", IssueModel.sprint)
        .add_simple_field("votes", IssueModel.votes)
        .add_simple_field("created", IssueModel.created)
        .add_lookup_field(
            "issuetype",
            IssueModel.issuetype_name,
            IssueModel.issuetype_id,
            aliases=["type"],
        )
        .add_lookup_field("status", IssueModel.status_name, IssueModel.status_id)
        .add_lookup_field("priority", IssueModel.priority_name, IssueModel.priority_id)
        .add_collection_field(
            "assignee",
            scalar_expression=IssueModel.assignees,
            collection_contains_builder=lambda val: IssueModel.assignees.any(
                func.lower(IssueAssigneeModel.username) == val.lower()
            ),
            collection_contains_substring_builder=lambda val: IssueModel.assignees.any(
                func.lower(IssueAssigneeModel.username).contains(val.lower())
            ),
            collection_is_empty_expression=~IssueModel.assignees.any(),
            collection_contains_by_id_builder=lambda uid: IssueModel.assignees.any(
                IssueAssigneeModel.user_id == uid
            ),
            collection_contains_by_ids_builder=lambda uids: IssueModel.assignees.any(
                IssueAssigneeModel.user_id.in_(uids)
            ),
        )
        .add_computed_field(
            "text",
            func.coalesce(IssueModel.summary, "")
            + " "
            + func.coalesce(IssueModel.description, ""),
        )
        .build()
    )
    return DynamicEntityFieldAccessor(registry)
