"""Backward-compatible re-export for builtin_resolver."""

from rql.functions.builtin_rql_function_resolver import BuiltInRqlFunctionResolver
from rql.functions.function_resolver_chain import FunctionResolverChain

__all__ = ["BuiltInRqlFunctionResolver", "FunctionResolverChain"]
