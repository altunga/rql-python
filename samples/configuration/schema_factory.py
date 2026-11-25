"""Sample RqlMetadata schema configuration for an Issue Tracking domain."""

from __future__ import annotations

from rql.metadata.schema import RqlField, RqlFunction, RqlMetadata


def create_sample_rql_metadata() -> RqlMetadata:
    """Creates an RqlMetadata instance populated with sample Issue Tracking fields and functions."""
    meta = RqlMetadata(
        fields=[
            RqlField("id", "number", []),
            RqlField("key", "text", []),
            RqlField("project", "text", ["CRM", "SUP", "DEV"]),
            RqlField("issuetype", "text", ["Bug", "Task", "Story", "Epic", "Sub-task"]),
            RqlField("type", "text", ["Bug", "Task", "Story", "Epic", "Sub-task"]),
            RqlField("status", "text", ["Open", "In Progress", "Resolved", "Closed"]),
            RqlField(
                "priority",
                "text",
                ["Blocker", "Critical", "High", "Medium", "Low", "Trivial"],
            ),
            RqlField("summary", "text", []),
            RqlField("description", "text", []),
            RqlField("text", "text", []),
            RqlField("assignee", "user", ["alice", "bob", "eren"]),
            RqlField("created", "date", []),
            RqlField("updated", "date", []),
            RqlField("sprint", "text", ["Sprint 1", "Sprint 2", "Sprint 3", "EMPTY"]),
            RqlField("labels", "text", ["auth", "security", "ui", "api", "performance"]),
            RqlField("votes", "number", []),
        ]
    )
    meta.add_function(
        RqlFunction("currentUser", "user", "Returns the currently logged-in user")
    ).add_function(
        RqlFunction("openSprints", "sprint", "Returns currently open sprints")
    )
    return meta
