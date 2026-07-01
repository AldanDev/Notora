---
name: notora-v2
description: Use when working with notora v2 models, repositories, services, query DSL, pagination, schemas, soft delete, actor-aware writes, or migration from legacy notora patterns. This skill provides bundled notora v2 references so agents do not guess APIs from memory.
---

# Notora v2

## Purpose

Use this skill to implement or review code that depends on `notora.v2`. Prefer the bundled references over memory. New code should use `notora.v2`; do not introduce new `notora.v1` usage unless maintaining existing legacy code.

## Reference Routing

Read only the references needed for the current task:

- Overview and topic map: `references/index.md`
- SQLAlchemy base models and mixins: `references/models.md`
- Repository classes, mixins, `RepoConfig`, `QueryParams`: `references/repositories.md`
- Service classes, `ServiceConfig`, raw vs serialized methods, actor-aware writes: `references/services.md`
- HTTP query filtering/sorting DSL, allowlisted fields, FastAPI dependency helpers: `references/query-dsl.md`
- Pagination response shape and no-limit behavior: `references/pagination.md`
- M2M sync helpers and modes: `references/m2m.md`
- Common patterns and endpoint recipes: `references/recipes.md`
- Term disambiguation for query/filter/order APIs: `references/glossary.md`

If exact signatures or implementation behavior matter and source code is available in the current environment, inspect the installed or local `notora.v2` source after reading the relevant bundled reference.

## Working Rules

- Use v2 imports such as `notora.v2.repositories`, `notora.v2.services`, `notora.v2.models.base`, and `notora.v2.schemas.base`.
- Prefer v2 repository/service base classes before writing custom SQL or custom execution helpers.
- Keep SQL construction in repositories/services, not app handlers.
- In service methods, prefer the service execution helpers documented in `references/services.md` over direct `session.execute(...)`.
- Use allowlists for query filters and sorting; do not expose arbitrary model fields to HTTP query parameters.
- Be explicit about `limit=None` vs omitted limit: `None` means no limit, omitted limit uses repository defaults.
- For writes with user attribution, pass `actor_id` only when the model supports the configured updated-by field.

## Integration With Host Projects

When this skill is copied into another repository, keep `references/` with it. Do not replace the bundled references with machine-local absolute paths. If upstream notora docs change, update this skill by copying the refreshed references from the notora repository.
