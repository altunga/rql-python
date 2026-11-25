"""In-memory RQL AST evaluator."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from functools import cmp_to_key
from typing import Any, Generic, TypeVar

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
from rql.backends.in_memory.predicate_visitor import InMemoryPredicateVisitor
from rql.strategies.operators import (
    ScalarOperatorRegistry,
    evaluate_scalar_operator,
)

T = TypeVar("T")
Predicate = Callable[[T], bool]


class InMemoryRqlExecutor(Generic[T]):
    """Evaluates RQL AST queries over in-memory Python iterables."""

    def __init__(
        self,
        field_accessors: Iterable[IEntityFieldAccessor[T]],
        function_resolvers: Iterable[IRqlFunctionResolver[T]],
        collection_accessor: ICollectionFieldAccessor[T],
        lookup_resolver: ILookupResolver,
        lookup_field_accessor: ILookupFieldAccessor[T],
        operator_registry: ScalarOperatorRegistry | None = None,
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
        self._operator_registry = operator_registry

    def execute(self, source: Iterable[T], query: RqlQuery) -> list[T]:
        """Applies RQL WHERE filter and ORDER BY to source and returns matching items."""
        items = list(source)
        if query.where is not None:
            predicate = self.build_predicate(query.where)
            items = [item for item in items if predicate(item)]

        if query.order_by is not None:
            items = self._apply_order_by(items, query.order_by)

        return items

    def build_predicate(self, node: RqlNode) -> Predicate[T]:
        """Builds a composable predicate Callable[[T], bool] from an RqlNode via Visitor."""
        visitor = InMemoryPredicateVisitor(self)
        return node.accept(visitor)

    def _build_condition_predicate(self, cond: FieldConditionNode) -> Predicate[T]:
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
        field_getter = self._get_field_getter(cond.field)
        op = cond.operator

        def _scalar_pred(entity: T) -> bool:
            val = field_getter(entity)
            if self._operator_registry is not None:
                return self._operator_registry.evaluate(
                    op, val, resolved_values, first_value, is_null
                )
            return evaluate_scalar_operator(op, val, resolved_values, first_value, is_null)

        return _scalar_pred

    def _build_lookup_condition(
        self,
        field: str,
        op: str,
        resolved_values: list[str],
        first_value: str,
    ) -> Predicate[T]:
        fk_getter: Callable[[T], int] = self._lookup_field_accessor.get_fk_expression(field)

        if op in ("=", "is", "was"):
            resolved_id = self._lookup_resolver.resolve(field, first_value)
            if resolved_id is None:
                return lambda _: False
            target_id = resolved_id
            return lambda e: fk_getter(e) == target_id

        if op in ("!=", "is not", "was not"):
            resolved_id = self._lookup_resolver.resolve(field, first_value)
            if resolved_id is None:
                return lambda _: True
            target_id = resolved_id
            return lambda e: fk_getter(e) != target_id

        if op in ("in", "was in"):
            ids = set(self._lookup_resolver.resolve_many(field, resolved_values))
            if not ids:
                return lambda _: False
            return lambda e: fk_getter(e) in ids

        if op in ("not in", "was not in"):
            ids = set(self._lookup_resolver.resolve_many(field, resolved_values))
            if not ids:
                return lambda _: True
            return lambda e: fk_getter(e) not in ids

        if op in ("<", "<=", ">", ">="):
            resolved_id = self._lookup_resolver.resolve(field, first_value)
            if resolved_id is None:
                return lambda _: False
            target_id = resolved_id
            if op == "<":
                return lambda e: fk_getter(e) < target_id
            if op == "<=":
                return lambda e: fk_getter(e) <= target_id
            if op == ">":
                return lambda e: fk_getter(e) > target_id
            return lambda e: fk_getter(e) >= target_id

        field_getter = self._get_field_getter(field)
        return lambda e: evaluate_scalar_operator(
            op, field_getter(e), resolved_values, first_value, False
        )

    def _build_collection_condition(
        self,
        field: str,
        op: str,
        values: list[str],
        first_value: str,
        is_null: bool,
    ) -> Predicate[T]:
        if (
            self._lookup_resolver.is_lookup_field(field)
            and op not in ("~", "!~")
            and not is_null
        ):
            by_id_pred = self._build_collection_condition_by_id(
                field, op, values, first_value
            )
            if by_id_pred is not None:
                return by_id_pred

        if op in ("=", "was"):
            fn: Predicate[T] = self._collection_accessor.get_collection_contains_expression(
                field, first_value
            )
            return fn

        if op in ("!=", "was not"):
            fn = self._collection_accessor.get_collection_contains_expression(
                field, first_value
            )
            return lambda e: not fn(e)

        if op == "~":
            sub_fn: Predicate[T] = (
                self._collection_accessor.get_collection_contains_substring_expression(
                    field, first_value
                )
            )
            return sub_fn

        if op == "!~":
            sub_fn = self._collection_accessor.get_collection_contains_substring_expression(
                field, first_value
            )
            return lambda e: not sub_fn(e)

        if op in ("in", "was in"):
            preds: list[Predicate[T]] = [
                self._collection_accessor.get_collection_contains_expression(field, v)
                for v in values
            ]
            if not preds:
                return lambda _: False
            return lambda e: any(p(e) for p in preds)

        if op in ("not in", "was not in"):
            preds = [
                self._collection_accessor.get_collection_contains_expression(field, v)
                for v in values
            ]
            if not preds:
                return lambda _: True
            return lambda e: not any(p(e) for p in preds)

        if op == "is":
            if is_null:
                empty_fn: Predicate[T] = (
                    self._collection_accessor.get_collection_is_empty_expression(field)
                )
                return empty_fn
            eq_fn: Predicate[T] = (
                self._collection_accessor.get_collection_contains_expression(
                    field, first_value
                )
            )
            return eq_fn

        if op == "is not":
            if is_null:
                empty_fn = self._collection_accessor.get_collection_is_empty_expression(
                    field
                )
                return lambda e: not empty_fn(e)
            eq_fn = self._collection_accessor.get_collection_contains_expression(
                field, first_value
            )
            return lambda e: not eq_fn(e)

        return lambda _: True

    def _build_collection_condition_by_id(
        self,
        field: str,
        op: str,
        values: list[str],
        first_value: str,
    ) -> Predicate[T] | None:
        if op in ("=", "is", "was"):
            user_id = self._lookup_resolver.resolve(field, first_value)
            if user_id is None:
                return None
            expr: Predicate[T] | None = (
                self._collection_accessor.get_collection_contains_by_id_expression(
                    field, user_id
                )
            )
            return expr

        if op in ("!=", "is not", "was not"):
            user_id = self._lookup_resolver.resolve(field, first_value)
            if user_id is None:
                return None
            expr = self._collection_accessor.get_collection_contains_by_id_expression(
                field, user_id
            )
            if expr is None:
                return None
            valid_expr = expr
            return lambda e: not valid_expr(e)

        if op in ("in", "was in"):
            user_ids = self._lookup_resolver.resolve_many(field, values)
            if not user_ids:
                return None
            expr = self._collection_accessor.get_collection_contains_by_ids_expression(
                field, user_ids
            )
            return expr

        if op in ("not in", "was not in"):
            user_ids = self._lookup_resolver.resolve_many(field, values)
            if not user_ids:
                return lambda _: True
            expr = self._collection_accessor.get_collection_contains_by_ids_expression(
                field, user_ids
            )
            if expr is None:
                return None
            valid_ids_expr = expr
            return lambda e: not valid_ids_expr(e)

        return None

    def _get_field_getter(self, field: str) -> Callable[[T], Any]:
        for accessor in self._field_accessors:
            if accessor.handles(field):
                matched_accessor = accessor
                return lambda e: matched_accessor.get_value(e, field)
        return lambda _: None

    def _apply_order_by(self, items: list[T], order_by: OrderByClause) -> list[T]:
        getters = [(self._get_field_getter(sf.field), sf.asc) for sf in order_by.fields]

        def _compare(a: T, b: T) -> int:
            for getter, asc in getters:
                va = getter(a)
                vb = getter(b)
                if va == vb:
                    continue
                if va is None:
                    res = -1
                elif vb is None:
                    res = 1
                else:
                    res = -1 if va < vb else 1
                return res if asc else -res
            return 0

        return sorted(items, key=cmp_to_key(_compare))
