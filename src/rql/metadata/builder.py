"""FieldMetadataBuilder implementing the GoF Builder pattern for FieldMetadataRegistry."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any, Generic, TypeVar, overload

from rql.metadata.field_metadata import (
    CollectionFieldMetadata,
    ComputedFieldMetadata,
    FieldMetadata,
    LookupFieldMetadata,
    SimpleFieldMetadata,
)
from rql.metadata.registry import FieldMetadataRegistry

T = TypeVar("T")


class FieldMetadataBuilder(Generic[T]):
    """Fluent Builder for constructing FieldMetadataRegistry instances (GoF Builder pattern)."""

    def __init__(self) -> None:
        self._fields: dict[str, FieldMetadata] = {}
        self._aliases: dict[str, list[str]] = {}

    @overload
    def add_simple_field(
        self,
        field_or_expr: str,
        expression: Any,
        aliases: Iterable[str] | None = None,
    ) -> FieldMetadataBuilder[T]: ...

    @overload
    def add_simple_field(
        self,
        field_or_expr: Any,
        expression: None = None,
        aliases: Iterable[str] | None = None,
    ) -> FieldMetadataBuilder[T]: ...

    def add_simple_field(
        self,
        field_or_expr: Any,
        expression: Any = None,
        aliases: Iterable[str] | None = None,
    ) -> FieldMetadataBuilder[T]:
        """Registers a simple scalar field with explicit or automatically extracted field name."""
        if isinstance(field_or_expr, str):
            field_name = field_or_expr
            expr = expression
        else:
            expr = field_or_expr
            field_name = self._extract_field_name(expr)

        value_getter = self._compile_value_getter(expr)
        metadata = SimpleFieldMetadata(
            name=field_name,
            field_type=object,
            value_getter=value_getter,
            expression_getter=lambda: expr,
        )
        self._fields[field_name.lower()] = metadata
        self._register_aliases(field_name, aliases)
        return self

    def add_lookup_field(
        self,
        field_name: Any = None,
        scalar_expression: Any = None,
        fk_expression: Any = None,
        aliases: Iterable[str] | None = None,
    ) -> FieldMetadataBuilder[T]:
        """Registers a lookup field (FK with scalar display property)."""
        resolved_name: str | None = None
        if isinstance(field_name, str):
            resolved_name = field_name
        elif field_name is not None:
            # Called with positional (scalar_expression, fk_expression[, aliases])
            aliases = fk_expression if fk_expression is not None else aliases
            fk_expression = scalar_expression
            scalar_expression = field_name

        if scalar_expression is None or fk_expression is None:
            raise ValueError("Both scalar_expression and fk_expression are required")

        if resolved_name is None:
            resolved_name = self._extract_field_name(fk_expression, remove_suffix="Id")

        value_getter = self._compile_value_getter(scalar_expression)
        metadata = LookupFieldMetadata(
            name=resolved_name,
            field_type=object,
            value_getter=value_getter,
            expression_getter=lambda: scalar_expression,
            fk_expression_getter=lambda: fk_expression,
        )
        self._fields[resolved_name.lower()] = metadata
        self._register_aliases(resolved_name, aliases)
        return self

    @overload
    def add_collection_field(
        self,
        field_or_scalar_expr: str,
        scalar_expression: Any,
        collection_contains_builder: Callable[[str], Any],
        collection_contains_substring_builder: Callable[[str], Any],
        collection_is_empty_expression: Any,
        collection_contains_by_id_builder: Callable[[int], Any] | None = None,
        collection_contains_by_ids_builder: Callable[[list[int]], Any] | None = None,
        aliases: Iterable[str] | None = None,
    ) -> FieldMetadataBuilder[T]: ...

    @overload
    def add_collection_field(
        self,
        field_or_scalar_expr: Any = None,
        scalar_expression: Any = None,
        collection_contains_builder: Any = None,
        collection_contains_substring_builder: Any = None,
        collection_is_empty_expression: Any = None,
        collection_contains_by_id_builder: Callable[[int], Any] | None = None,
        collection_contains_by_ids_builder: Callable[[list[int]], Any] | None = None,
        aliases: Iterable[str] | None = None,
    ) -> FieldMetadataBuilder[T]: ...

    def add_collection_field(
        self,
        field_or_scalar_expr: Any = None,
        scalar_expression: Any = None,
        collection_contains_builder: Any = None,
        collection_contains_substring_builder: Any = None,
        collection_is_empty_expression: Any = None,
        collection_contains_by_id_builder: Callable[[int], Any] | None = None,
        collection_contains_by_ids_builder: Callable[[list[int]], Any] | None = None,
        aliases: Iterable[str] | None = None,
    ) -> FieldMetadataBuilder[T]:
        """Registers a many-to-many collection field with full filtering support."""
        if isinstance(field_or_scalar_expr, str):
            field_name = field_or_scalar_expr
            scalar_expr = scalar_expression
        elif field_or_scalar_expr is not None:
            # Positional call without field_name: shift positional arguments
            if scalar_expression is not None and collection_is_empty_expression is None:
                aliases = collection_contains_by_ids_builder  # type: ignore[assignment]
                collection_contains_by_ids_builder = collection_contains_by_id_builder  # type: ignore[assignment]
                collection_contains_by_id_builder = collection_is_empty_expression
                collection_is_empty_expression = collection_contains_substring_builder
                collection_contains_substring_builder = collection_contains_builder
                collection_contains_builder = scalar_expression
            scalar_expr = field_or_scalar_expr
            field_name = self._extract_field_name(scalar_expr, singularize=True)
        elif scalar_expression is not None:
            scalar_expr = scalar_expression
            field_name = self._extract_field_name(scalar_expr, singularize=True)
        else:
            raise ValueError("scalar_expression is required for collection field")

        if (
            scalar_expr is None
            or collection_contains_builder is None
            or collection_contains_substring_builder is None
            or collection_is_empty_expression is None
        ):
            raise ValueError(
                "Collection field requires scalar_expression, collection_contains_builder, "
                "collection_contains_substring_builder, and collection_is_empty_expression"
            )

        contains_fn = collection_contains_builder
        substring_fn = collection_contains_substring_builder
        empty_expr = collection_is_empty_expression
        by_id_fn = collection_contains_by_id_builder
        by_ids_fn = collection_contains_by_ids_builder

        value_getter = self._compile_value_getter(scalar_expr)
        metadata = CollectionFieldMetadata(
            name=field_name,
            field_type=object,
            value_getter=value_getter,
            expression_getter=lambda: scalar_expr,
            collection_contains_getter=lambda val: contains_fn(val),
            collection_contains_substring_getter=lambda val: substring_fn(val),
            collection_is_empty_getter=lambda: empty_expr,
            collection_contains_by_id_getter=(
                None if by_id_fn is None else (lambda id_val: by_id_fn(id_val))
            ),
            collection_contains_by_ids_getter=(
                None if by_ids_fn is None else (lambda ids: by_ids_fn(ids))
            ),
        )
        self._fields[field_name.lower()] = metadata
        self._register_aliases(field_name, aliases)
        return self

    def add_computed_field(
        self,
        field_name: str,
        expression: Any,
        aliases: Iterable[str] | None = None,
    ) -> FieldMetadataBuilder[T]:
        """Registers a computed field (e.g. 'text' = Summary + Description)."""
        if not isinstance(field_name, str) or not field_name.strip():
            raise ValueError("Computed fields require an explicit non-empty field_name")

        value_getter = self._compile_value_getter(expression)
        metadata = ComputedFieldMetadata(
            name=field_name,
            field_type=str,
            value_getter=value_getter,
            expression_getter=lambda: expression,
        )
        self._fields[field_name.lower()] = metadata
        self._register_aliases(field_name, aliases)
        return self

    def add_alias(self, canonical: str, alias: str) -> FieldMetadataBuilder[T]:
        """Registers an alias for an already-registered canonical field."""
        key = canonical.lower()
        if key not in self._fields:
            raise ValueError(f"Canonical field '{canonical}' not registered")

        if key not in self._aliases:
            self._aliases[key] = []
        self._aliases[key].append(alias.lower())
        return self

    def build(self) -> FieldMetadataRegistry[T]:
        """Builds the immutable FieldMetadataRegistry."""
        if not self._fields:
            raise ValueError("No fields registered")
        return FieldMetadataRegistry(self._fields, self._aliases)

    def _register_aliases(
        self, canonical: str, aliases: Iterable[str] | None
    ) -> None:
        if aliases is None:
            return
        key = canonical.lower()
        if key not in self._aliases:
            self._aliases[key] = []
        for alias in aliases:
            self._aliases[key].append(alias.lower())

    @staticmethod
    def _compile_value_getter(expr: Any) -> Callable[[Any], Any]:
        # SQLAlchemy InstrumentedAttribute or descriptor with .key
        if hasattr(expr, "key") and isinstance(expr.key, str):
            attr_name = expr.key
            return lambda entity: getattr(entity, attr_name, None)
        if callable(expr):
            return lambda entity: expr(entity)
        if isinstance(expr, property) and expr.fget is not None:
            fget = expr.fget
            return lambda entity: fget(entity)
        return lambda _: None

    def _extract_field_name(
        self,
        expression: Any,
        remove_suffix: str | None = None,
        singularize: bool = False,
    ) -> str:
        raw_name = self._extract_raw_property_name(expression)
        if not raw_name:
            raise ValueError(f"Expression does not resolve to a property: {expression!r}")

        name = raw_name
        if remove_suffix:
            if name.endswith(remove_suffix):
                name = name[: -len(remove_suffix)]
            elif name.lower().endswith("_" + remove_suffix.lower()):
                name = name[: -(len(remove_suffix) + 1)]

        if singularize:
            name = self._singularize(name)

        return self._to_camel_case(name)

    @staticmethod
    def _extract_raw_property_name(expression: Any) -> str | None:
        # 1. SQLAlchemy InstrumentedAttribute / Column
        if hasattr(expression, "key") and isinstance(expression.key, str):
            return expression.key
        if hasattr(expression, "name") and isinstance(expression.name, str):
            return expression.name
        # 2. Python @property
        if isinstance(expression, property) and expression.fget is not None:
            return str(expression.fget.__name__)
        # 3. Lambda / function inspecting single attribute access via bytecode co_names
        if callable(expression) and hasattr(expression, "__code__"):
            co_names: tuple[str, ...] = expression.__code__.co_names
            if len(co_names) == 1:
                return co_names[0]
        return None

    @staticmethod
    def _to_camel_case(name: str) -> str:
        if not name:
            return name
        if "_" in name:
            parts = [p for p in name.split("_") if p]
            if not parts:
                return name
            return parts[0].lower() + "".join(p.capitalize() for p in parts[1:])
        if len(name) == 1:
            return name.lower()
        return name[0].lower() + name[1:]

    @staticmethod
    def _singularize(name: str) -> str:
        if not name:
            return name
        if name.endswith("ies") and len(name) > 3:
            return name[:-3] + "y"
        if name.endswith("es") and len(name) > 2 and (
            name.endswith(("sses", "xes", "zes", "ches", "shes"))
        ):
            return name[:-2]
        if name.endswith("s") and len(name) > 1:
            return name[:-1]
        return name
