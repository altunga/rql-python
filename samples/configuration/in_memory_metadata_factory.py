"""Factory building FieldMetadataRegistry and DynamicEntityFieldAccessor for in-memory Issue."""

from __future__ import annotations

from rql.metadata import DynamicEntityFieldAccessor, FieldMetadataBuilder
from samples.models.in_memory.issue import Issue


def create_in_memory_accessor() -> DynamicEntityFieldAccessor[Issue]:
    """Configures Simple, Lookup, Collection, and Computed fields for the in-memory Issue model."""
    builder: FieldMetadataBuilder[Issue] = FieldMetadataBuilder()
    registry = (
        builder.add_simple_field(lambda i: i.Id)
        .add_simple_field(lambda i: i.Key)
        .add_simple_field(lambda i: i.ProjectKey, aliases=["project"])
        .add_simple_field(lambda i: i.Summary)
        .add_simple_field(lambda i: i.Description)
        .add_simple_field(lambda i: i.Sprint)
        .add_simple_field(lambda i: i.Votes)
        .add_simple_field(lambda i: i.Created)
        .add_simple_field(lambda i: i.Updated)
        # Lookup fields (automatically strips 'Id' suffix -> issueType, status, priority)
        .add_lookup_field(
            scalar_expression=lambda i: i.IssueTypeName,
            fk_expression=lambda i: i.IssueTypeId,
            aliases=["type"],
        )
        .add_lookup_field(
            scalar_expression=lambda i: i.StatusName,
            fk_expression=lambda i: i.StatusId or 0,
        )
        .add_lookup_field(
            scalar_expression=lambda i: i.PriorityName,
            fk_expression=lambda i: i.PriorityId,
        )
        # Collection field with ID lookup + string matching (Assignees -> assignee)
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
        # String collection field (Labels -> label, with alias 'labels')
        .add_collection_field(
            scalar_expression=lambda i: i.Labels,
            collection_contains_builder=lambda val: (
                lambda i: any(lbl.lower() == val.lower() for lbl in i.Labels)
            ),
            collection_contains_substring_builder=lambda val: (
                lambda i: any(val.lower() in lbl.lower() for lbl in i.Labels)
            ),
            collection_is_empty_expression=lambda i: len(i.Labels) == 0,
            aliases=["labels"],
        )
        # Computed field combining Summary + Description
        .add_computed_field("text", lambda i: f"{i.Summary} {i.Description or ''}")
        .build()
    )
    return DynamicEntityFieldAccessor(registry)
