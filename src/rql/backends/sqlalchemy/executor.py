"""SQLAlchemy 2.0 RQL AST evaluator."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import datetime, timezone
from typing import Any, Generic, TypeVar, cast

from sqlalchemy import String, and_, asc, cast as sa_cast, desc, false, func, not_, or_, true
from sqlalchemy.sql import ColumnElement, Select

from rql.abstractions.accessors import (
    ICollectionFieldAccessor,
    IEntityFieldAccessor,
    ILookupFieldAccessor,
    ILookupResolver,
)
from rql.abstractions.functions import IRqlFunctionResolver
from rql.ast.nodes import (
    FieldConditionNode,
    OrderByClause,
    RqlNode,
    RqlQuery,
)
from rql.backends.base import logger, resolve_condition_values
from rql.backends.sqlalchemy.predicate_visitor import SqlAlchemyPredicateVisitor

T = TypeVar("T")
TSelect = TypeVar("TSelect", bound=Select[Any])


class SqlAlchemyRqlExecutor(Generic[T]):
    """Translates RQL AST queries into SQLAlchemy 2.0 Select statements."""

    def __init__(
        self,
        field_accessors: Iterable[IEntityFieldAccessor[T]],
        function_resolvers: Iterable[IRqlFunctionResolver[T]],
        collection_accessor: ICollectionFieldAccessor[T],
        lookup_resolver: ILookupResolver,
        lookup_field_accessor: ILookupFieldAccessor[T],
    ) -> None:
        if field_accessors is None:
            raise ValueError("field_accessors must not be None")
        if function_resolvers is None:
            raise ValueError("function_resolvers must not be None")
        if collection_accessor is None:
            raise ValueError("collection_accessor must not be None")
        if lookup_resolver is None:
            raise ValueError("lookup_resolver must not be None")
        if lookup_field_accessor is None:
            raise ValueError("lookup_field_accessor must not be None")

        self._field_accessors = list(field_accessors)
        self._function_resolvers = list(function_resolvers)
        self._collection_accessor = collection_accessor
        self._lookup_resolver = lookup_resolver
        self._lookup_field_accessor = lookup_field_accessor

    def execute(self, source: TSelect, query: RqlQuery) -> TSelect:
        """Applies RQL WHERE filter and ORDER BY to a SQLAlchemy Select statement."""
        stmt: Any = source
        if query.where is not None:
            predicate = self.build_predicate(query.where)
            stmt = stmt.where(predicate)

        if query.order_by is not None:
            stmt = self._apply_order_by(stmt, query.order_by)

        return cast(TSelect, stmt)

    def build_predicate(self, node: RqlNode) -> ColumnElement[bool]:
        """Builds a SQLAlchemy ColumnElement[bool] predicate from an RqlNode via Visitor."""
        visitor = SqlAlchemyPredicateVisitor(self)
        return node.accept(visitor)

    def _build_condition_expression(self, cond: FieldConditionNode) -> ColumnElement[bool]:
        resolved_values, first_value, is_null = resolve_condition_values(
            cond.values, self._function_resolvers
        )

        is_collection = self._collection_accessor.is_collection_field(cond.field)
        is_lookup = self._lookup_resolver.is_lookup_field(
            cond.field
        ) and self._lookup_field_accessor.is_lookup_field(cond.field)

        logger.debug(
            "[RQL DEBUG] Field='%s' IsCollection=%s IsLookup=%s Op=%s Val='%s'",
            cond.field,
            is_collection,
            is_lookup,
            cond.operator,
            first_value,
        )

        if is_collection:
            logger.debug("[RQL DEBUG] -> Using COLLECTION path")
            return self._build_collection_condition(
                cond.field, cond.operator, resolved_values, first_value, is_null
            )

        if is_lookup and not is_null:
            logger.debug("[RQL DEBUG] -> Using LOOKUP path")
            return self._build_lookup_condition(
                cond.field, cond.operator, resolved_values, first_value
            )

        logger.debug("[RQL DEBUG] -> Using SCALAR path")
        field_expr = self._get_field_expression(cond.field)
        op = cond.operator
        if field_expr is None:
            return self._build_null_field_fallback(op, is_null)

        if op in ("=", "was"):
            return self._build_equals(field_expr, first_value)
        if op in ("!=", "was not"):
            return not_(self._build_equals(field_expr, first_value))
        if op in ("<", "<=", ">", ">="):
            return self._build_compare(field_expr, first_value, op)
        if op == "~":
            return self._build_contains(field_expr, first_value)
        if op == "!~":
            return not_(self._build_contains(field_expr, first_value))
        if op in ("in", "was in"):
            return self._build_in(field_expr, resolved_values)
        if op in ("not in", "was not in"):
            return not_(self._build_in(field_expr, resolved_values))
        if op == "is":
            return (
                self._build_is_null(field_expr)
                if is_null
                else self._build_equals(field_expr, first_value)
            )
        if op == "is not":
            return (
                not_(self._build_is_null(field_expr))
                if is_null
                else not_(self._build_equals(field_expr, first_value))
            )
        return true()

    @staticmethod
    def _build_null_field_fallback(op: str, is_null: bool) -> ColumnElement[bool]:
        """Matches C# e => null fallback when a field is not registered in metadata."""
        if op == "is":
            return true() if is_null else false()
        if op == "is not":
            return false() if is_null else true()
        if op in ("!=", "!~", "not in", "was not", "was not in", "changed"):
            return true()
        return false()

    def _build_lookup_condition(
        self,
        field: str,
        op: str,
        resolved_values: list[str],
        first_value: str,
    ) -> ColumnElement[bool]:
        fk_expr: Any = self._lookup_field_accessor.get_fk_expression(field)

        if op in ("=", "is", "was"):
            resolved_id = self._lookup_resolver.resolve(field, first_value)
            if resolved_id is None:
                return false()
            return and_(fk_expr.is_not(None), cast(ColumnElement[bool], fk_expr == resolved_id))

        if op in ("!=", "is not", "was not"):
            resolved_id = self._lookup_resolver.resolve(field, first_value)
            if resolved_id is None:
                return true()
            return not_(
                and_(fk_expr.is_not(None), cast(ColumnElement[bool], fk_expr == resolved_id))
            )

        if op in ("in", "was in"):
            ids = self._lookup_resolver.resolve_many(field, resolved_values)
            if not ids:
                return false()
            return and_(fk_expr.is_not(None), cast(ColumnElement[bool], fk_expr.in_(ids)))

        if op in ("not in", "was not in"):
            ids = self._lookup_resolver.resolve_many(field, resolved_values)
            if not ids:
                return true()
            return not_(
                and_(fk_expr.is_not(None), cast(ColumnElement[bool], fk_expr.in_(ids)))
            )

        if op in ("<", "<=", ">", ">="):
            resolved_id = self._lookup_resolver.resolve(field, first_value)
            if resolved_id is None:
                return false()
            if op == "<":
                return cast(ColumnElement[bool], fk_expr < resolved_id)
            if op == "<=":
                return cast(ColumnElement[bool], fk_expr <= resolved_id)
            if op == ">":
                return cast(ColumnElement[bool], fk_expr > resolved_id)
            return cast(ColumnElement[bool], fk_expr >= resolved_id)

        field_expr = self._get_field_expression(field)
        if field_expr is None:
            return self._build_null_field_fallback(op, False)
        if op == "~":
            return self._build_contains(field_expr, first_value)
        if op == "!~":
            return not_(self._build_contains(field_expr, first_value))
        return true()

    def _build_collection_condition(
        self,
        field: str,
        op: str,
        values: list[str],
        first_value: str,
        is_null: bool,
    ) -> ColumnElement[bool]:
        if (
            self._lookup_resolver.is_lookup_field(field)
            and op not in ("~", "!~")
            and not is_null
        ):
            by_id_expr = self._build_collection_condition_by_id(
                field, op, values, first_value
            )
            if by_id_expr is not None:
                return by_id_expr

        if op in ("=", "was"):
            return cast(
                ColumnElement[bool],
                self._collection_accessor.get_collection_contains_expression(
                    field, first_value
                ),
            )
        if op in ("!=", "was not"):
            return not_(
                cast(
                    ColumnElement[bool],
                    self._collection_accessor.get_collection_contains_expression(
                        field, first_value
                    ),
                )
            )
        if op == "~":
            return cast(
                ColumnElement[bool],
                self._collection_accessor.get_collection_contains_substring_expression(
                    field, first_value
                ),
            )
        if op == "!~":
            return not_(
                cast(
                    ColumnElement[bool],
                    self._collection_accessor.get_collection_contains_substring_expression(
                        field, first_value
                    ),
                )
            )
        if op in ("in", "was in"):
            clauses = [
                cast(
                    ColumnElement[bool],
                    self._collection_accessor.get_collection_contains_expression(
                        field, v
                    ),
                )
                for v in values
            ]
            return or_(*clauses) if clauses else false()
        if op in ("not in", "was not in"):
            clauses = [
                cast(
                    ColumnElement[bool],
                    self._collection_accessor.get_collection_contains_expression(
                        field, v
                    ),
                )
                for v in values
            ]
            return not_(or_(*clauses)) if clauses else true()
        if op == "is":
            if is_null:
                return cast(
                    ColumnElement[bool],
                    self._collection_accessor.get_collection_is_empty_expression(field),
                )
            return cast(
                ColumnElement[bool],
                self._collection_accessor.get_collection_contains_expression(
                    field, first_value
                ),
            )
        if op == "is not":
            if is_null:
                return not_(
                    cast(
                        ColumnElement[bool],
                        self._collection_accessor.get_collection_is_empty_expression(
                            field
                        ),
                    )
                )
            return not_(
                cast(
                    ColumnElement[bool],
                    self._collection_accessor.get_collection_contains_expression(
                        field, first_value
                    ),
                )
            )
        return true()

    def _build_collection_condition_by_id(
        self,
        field: str,
        op: str,
        values: list[str],
        first_value: str,
    ) -> ColumnElement[bool] | None:
        if op in ("=", "is", "was"):
            user_id = self._lookup_resolver.resolve(field, first_value)
            if user_id is None:
                return None
            expr = self._collection_accessor.get_collection_contains_by_id_expression(
                field, user_id
            )
            return cast(ColumnElement[bool], expr) if expr is not None else None

        if op in ("!=", "is not", "was not"):
            user_id = self._lookup_resolver.resolve(field, first_value)
            if user_id is None:
                return None
            expr = self._collection_accessor.get_collection_contains_by_id_expression(
                field, user_id
            )
            return not_(cast(ColumnElement[bool], expr)) if expr is not None else None

        if op in ("in", "was in"):
            user_ids = self._lookup_resolver.resolve_many(field, values)
            if not user_ids:
                return None
            expr = self._collection_accessor.get_collection_contains_by_ids_expression(
                field, user_ids
            )
            return cast(ColumnElement[bool], expr) if expr is not None else None

        if op in ("not in", "was not in"):
            user_ids = self._lookup_resolver.resolve_many(field, values)
            if not user_ids:
                return true()
            expr = self._collection_accessor.get_collection_contains_by_ids_expression(
                field, user_ids
            )
            return not_(cast(ColumnElement[bool], expr)) if expr is not None else None

        return None

    @staticmethod
    def _build_equals(field_expr: Any, value: str) -> ColumnElement[bool]:
        lowered = func.lower(sa_cast(field_expr, String))
        return and_(field_expr.is_not(None), lowered == value.lower())

    @staticmethod
    def _build_contains(field_expr: Any, value: str) -> ColumnElement[bool]:
        lowered = func.lower(sa_cast(field_expr, String))
        return and_(field_expr.is_not(None), lowered.contains(value.lower()))

    @classmethod
    def _build_in(
        cls, field_expr: Any, values: Sequence[str]
    ) -> ColumnElement[bool]:
        if not values:
            return false()
        return or_(*(cls._build_equals(field_expr, v) for v in values))

    @staticmethod
    def _build_is_null(field_expr: Any) -> ColumnElement[bool]:
        return or_(field_expr.is_(None), sa_cast(field_expr, String) == "")

    @staticmethod
    def _build_compare(
        field_expr: Any, value: str, op: str
    ) -> ColumnElement[bool]:
        target: Any = value
        try:
            target = float(value) if "." in value else int(value)
        except ValueError:
            try:
                dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
                target = dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)
            except ValueError:
                field_expr = func.lower(sa_cast(field_expr, String))
                target = value.lower()

        if op == "<":
            return cast(ColumnElement[bool], field_expr < target)
        if op == "<=":
            return cast(ColumnElement[bool], field_expr <= target)
        if op == ">":
            return cast(ColumnElement[bool], field_expr > target)
        return cast(ColumnElement[bool], field_expr >= target)

    def _apply_order_by(
        self, stmt: Select[tuple[T]], order_by: OrderByClause
    ) -> Select[tuple[T]]:
        for sf in order_by.fields:
            expr = self._get_field_expression(sf.field)
            if expr is not None:
                stmt = stmt.order_by(asc(expr) if sf.asc else desc(expr))
        return stmt

    def _get_field_expression(self, field: str) -> Any:
        for accessor in self._field_accessors:
            if accessor.handles(field):
                return accessor.get_expression(field)
        return None
