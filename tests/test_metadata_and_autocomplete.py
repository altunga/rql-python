"""Unit tests for RqlMetadata, RqlMetadataService, and RqlAutocompleteService."""

from __future__ import annotations

from rql.metadata.schema import RqlField, RqlFunction, RqlMetadata
from rql.services.autocomplete_service import RqlAutocompleteService
from rql.services.metadata_service import RqlMetadataService


def _build_test_metadata() -> RqlMetadata:
    meta = RqlMetadata(
        fields=[
            RqlField("code", "text", ["ALPHA", "BETA", "GAMMA"]),
            RqlField("state", "text", []),
            RqlField("severity", "text", ["Critical", "High", "Medium", "Low"]),
            RqlField("title", "text", []),
            RqlField("timestamp", "date", []),
        ]
    )
    meta.add_function(RqlFunction("currentActor", "user", "Returns active actor"))
    return meta


def test_default_metadata_is_domain_agnostic() -> None:
    default_meta = RqlMetadata()
    assert default_meta.fields == []
    assert len(default_meta.operators) == 17
    assert len(default_meta.functions) == 11


def test_metadata_service_returns_configured_schema() -> None:
    meta = _build_test_metadata()
    service = RqlMetadataService(meta)
    response = service.get_metadata()

    assert len(response.fields) == 5
    assert len(response.operators) == 17
    assert len(response.functions) == 12
    assert response.keywords == [
        "AND",
        "OR",
        "NOT",
        "IN",
        "IS",
        "WAS",
        "CHANGED",
        "ORDER BY",
        "ASC",
        "DESC",
        "EMPTY",
        "NULL",
    ]
    code_field = meta.get_field("CODE")
    assert code_field is not None
    assert code_field.allowed_values == ["ALPHA", "BETA", "GAMMA"]


def test_autocomplete_field_and_function_suggestions() -> None:
    service = RqlAutocompleteService(_build_test_metadata())

    # Empty field -> suggests matching field names and functions with ()
    res = service.get_suggestions(field=None, query="st")
    assert "state" in res.suggestions
    assert "startOfDay()" in res.suggestions
    assert "startOfWeek()" in res.suggestions


def test_autocomplete_value_suggestions_for_enum_date_and_unknown_fields() -> None:
    service = RqlAutocompleteService(_build_test_metadata())

    # Field with allowed values uses case-insensitive substring match
    sev_res = service.get_suggestions(field="Severity", query="ig")
    assert sev_res.suggestions == ["High"]

    # Date field suggests date functions starting with prefix
    date_res = service.get_suggestions(field="timestamp", query="startOf")
    assert date_res.suggestions == [
        "startOfDay()",
        "startOfWeek()",
        "startOfMonth()",
        "startOfYear()",
    ]

    # Text field without allowed values or unknown field returns empty list
    assert service.get_suggestions(field="title", query="abc").suggestions == []
    assert service.get_suggestions(field="nonexistent", query="x").suggestions == []
