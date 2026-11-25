# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2026-11-26

### Added
- Full RQL (JQL-inspired) lexer and recursive-descent parser producing immutable AST nodes.
- Canonical query normalizer, syntax validator, schema metadata service, and prefix-based autocomplete service.
- Built-in UTC date and user functions (`now()`, `startOfDay()`, `endOfDay()`, `startOfWeek()`, `endOfWeek()`, `startOfMonth()`, `endOfMonth()`, `startOfYear()`, `endOfYear()`, `lastLogin()`, `membersOf()`), plus custom function resolver support.
- Dynamic field metadata builder supporting simple, foreign-key lookup, collection, and computed fields with automatic naming and alias resolution.
- Zero-dependency in-memory query executor and paginated search service.
- SQLAlchemy 2.0 query executor and paginated search service with direct foreign-key lookup optimization and `.any()` collection predicates.
- Unified `RqlEngine` entry point and runnable `samples/` showcase project.
