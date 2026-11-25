"""GoF Strategy pattern for scalar RQL operators (SRP & OCP)."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import datetime, timezone
from typing import Any


def is_null_or_empty_token(value: str) -> bool:
    """Returns True if the RQL literal value represents EMPTY or NULL."""
    return value.upper() in ("EMPTY", "NULL")


def is_field_value_null_or_empty(field_val: Any) -> bool:
    """Returns True if an entity's runtime field value is None or empty string."""
    if field_val is None:
        return True
    return str(field_val) == ""


def scalar_equals(field_val: Any, target: str) -> bool:
    """Case-insensitive string equality matching C# BuildEquals."""
    if field_val is None:
        return False
    return str(field_val).lower() == target.lower()


def scalar_contains(field_val: Any, target: str) -> bool:
    """Case-insensitive substring check matching C# BuildContains."""
    if field_val is None:
        return False
    return target.lower() in str(field_val).lower()


def _try_parse_datetime(raw: Any) -> datetime | None:
    if isinstance(raw, datetime):
        return raw if raw.tzinfo is not None else raw.replace(tzinfo=timezone.utc)
    if not isinstance(raw, str) or not raw:
        return None
    # Avoid parsing plain numbers like "10" or "2026" as dates if they are numeric
    try:
        float(raw)
        return None
    except ValueError:
        pass
    try:
        normalized = raw.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
        return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _try_parse_float(raw: Any) -> float | None:
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        return float(raw)
    if isinstance(raw, str):
        try:
            return float(raw)
        except ValueError:
            return None
    return None


def scalar_compare(field_val: Any, target: str, op: str) -> bool:
    """Compares field_val and target using datetime, numeric, or case-insensitive string ordering."""
    if field_val is None:
        return False

    target_dt = _try_parse_datetime(target)
    if target_dt is not None:
        field_dt = _try_parse_datetime(field_val)
        if field_dt is None:
            return False
        return _apply_order_op(field_dt, target_dt, op)

    target_num = _try_parse_float(target)
    if target_num is not None:
        field_num = _try_parse_float(field_val)
        if field_num is None:
            return False
        return _apply_order_op(field_num, target_num, op)

    return _apply_order_op(str(field_val).lower(), target.lower(), op)


def _apply_order_op(left: Any, right: Any, op: str) -> bool:
    if op == "<":
        return bool(left < right)
    if op == "<=":
        return bool(left <= right)
    if op == ">":
        return bool(left > right)
    if op == ">=":
        return bool(left >= right)
    return False


OperatorStrategyFn = Callable[[Any, Sequence[str], str, bool], bool]


class ScalarOperatorRegistry:
    """Registry of scalar operator evaluation strategies (OCP: register custom operators at runtime)."""

    def __init__(self) -> None:
        self._strategies: dict[str, OperatorStrategyFn] = {
            "=": lambda fv, vals, first, is_null: scalar_equals(fv, first),
            "!=": lambda fv, vals, first, is_null: not scalar_equals(fv, first),
            "<": lambda fv, vals, first, is_null: scalar_compare(fv, first, "<"),
            "<=": lambda fv, vals, first, is_null: scalar_compare(fv, first, "<="),
            ">": lambda fv, vals, first, is_null: scalar_compare(fv, first, ">"),
            ">=": lambda fv, vals, first, is_null: scalar_compare(fv, first, ">="),
            "~": lambda fv, vals, first, is_null: scalar_contains(fv, first),
            "!~": lambda fv, vals, first, is_null: not scalar_contains(fv, first),
            "in": lambda fv, vals, first, is_null: any(scalar_equals(fv, v) for v in vals),
            "not in": lambda fv, vals, first, is_null: not any(
                scalar_equals(fv, v) for v in vals
            ),
            "is": lambda fv, vals, first, is_null: (
                is_field_value_null_or_empty(fv)
                if is_null
                else scalar_equals(fv, first)
            ),
            "is not": lambda fv, vals, first, is_null: (
                not is_field_value_null_or_empty(fv)
                if is_null
                else not scalar_equals(fv, first)
            ),
            "was": lambda fv, vals, first, is_null: scalar_equals(fv, first),
            "was in": lambda fv, vals, first, is_null: any(
                scalar_equals(fv, v) for v in vals
            ),
            "was not": lambda fv, vals, first, is_null: not scalar_equals(fv, first),
            "was not in": lambda fv, vals, first, is_null: not any(
                scalar_equals(fv, v) for v in vals
            ),
            "changed": lambda fv, vals, first, is_null: True,
        }

    def register(self, operator: str, strategy: OperatorStrategyFn) -> None:
        """Registers or overrides an operator evaluation strategy."""
        self._strategies[operator.lower()] = strategy

    def evaluate(
        self,
        operator: str,
        field_val: Any,
        resolved_values: Sequence[str],
        first_value: str,
        is_null: bool,
    ) -> bool:
        strategy = self._strategies.get(operator.lower())
        if strategy is None:
            return True
        return strategy(field_val, resolved_values, first_value, is_null)


_DEFAULT_REGISTRY = ScalarOperatorRegistry()


def evaluate_scalar_operator(
    operator: str,
    field_val: Any,
    resolved_values: Sequence[str],
    first_value: str,
    is_null: bool,
) -> bool:
    """Evaluates a scalar operator using the default ScalarOperatorRegistry."""
    return _DEFAULT_REGISTRY.evaluate(
        operator, field_val, resolved_values, first_value, is_null
    )
