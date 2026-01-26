# Repositories (v2)

Repositories build SQLAlchemy statements using mixins and are safe to compose.

## Base classes

- `Repository[PKType, ModelType]`
- `SoftDeleteRepository[PKType, ModelType]`

Both expose methods from mixins and accept optional `RepoConfig` to override
defaults.

## Mixins

Query mixins:
- `SelectableMixin` -> `select()`
- `ListableMixin` -> `list()` / `list_by_params()`
- `RetrievableMixin` -> `retrieve()` / `retrieve_by()` / `retrieve_one_by()`
- `CountableMixin` -> `count()`

Write mixins:
- `CreateMixin` -> `create()` / `bulk_create()`
- `CreateOrSkipMixin` -> `create_or_skip()`
- `UpsertMixin` -> `upsert()`
- `UpdateMixin` -> `update()` / `update_by()`
- `DeleteMixin` -> `delete()` / `delete_by()`
- `SoftDeleteMixin` -> `soft_delete()` / `soft_delete_by()`

## RepoConfig

`RepoConfig` lets you override defaults on construction:

- `default_limit`
- `default_options`
- `default_filters`
- `default_ordering`
- `fallback_sort_attribute`
- `pk_attribute`
- `apply_soft_delete_filter` (only for `SoftDeleteRepository`)

Example:

```python
from notora.v2.repositories import Repository, RepoConfig

repo = Repository(User, config=RepoConfig(default_limit=25, pk_attribute="id"))
```

## QueryParams

`QueryParams` is a lightweight carrier used by repositories/services:

```python
from notora.v2.repositories import QueryParams

params = QueryParams(filters=[...], ordering=[...], limit=None, offset=0)
query = repo.list_by_params(params)
```

Notes:
- `limit=None` means "no limit".
- When `limit` is omitted, the repository uses `default_limit`.

## Detailed examples

### Basic listing with filters and ordering

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from notora.v2.repositories import Repository

repo = Repository(User)

async def list_active_users(session: AsyncSession) -> list[User]:
    # Use lambda to build a filter clause on the model
    query = repo.list(
        filters=[lambda m: m.is_active.is_(True)],
        ordering=[lambda m: m.created_at.desc()],
        limit=20,
        offset=0,
    )
    return (await session.scalars(query)).all()
```

### Basic listing without lambda

```python
async def list_active_users(session: AsyncSession) -> list[User]:
    # Direct SQLAlchemy clauses are also accepted
    query = repo.list(
        filters=[User.is_active.is_(True)],
        ordering=[User.created_at.desc()],
        limit=20,
        offset=0,
    )
    return (await session.scalars(query)).all()
```

### List with base_query and options

```python
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# Build a custom query (join/filters/etc)
base_query = select(User).where(User.is_active.is_(True))

# Apply loader options through list()
query = repo.list(
    base_query=base_query,
    options=[selectinload(User.profile)],
    limit=50,
)
```

### Create or skip (insert ignore)

```python
query = repo.create_or_skip(
    {"email": "a@b.com", "name": "Alice"},
    conflict_columns=[User.email],
)
entity = (await session.scalars(query)).one_or_none()
```

### Upsert with limited update fields

```python
query = repo.upsert(
    {"email": "a@b.com", "name": "Alice", "status": "active"},
    conflict_columns=[User.email],
    update_only=["name", "status"],  # only these fields update on conflict
)
entity = (await session.scalars(query)).one()
```

### RepoConfig with defaults

```python
from notora.v2.repositories import RepoConfig

repo = Repository(
    User,
    config=RepoConfig(
        default_limit=25,
        pk_attribute="id",
    ),
)
```

### SoftDeleteRepository defaults

`SoftDeleteRepository` automatically excludes soft-deleted rows by adding
`deleted_at IS NULL` to `default_filters`.

To include deleted rows, disable the filter:

```python
repo = SoftDeleteRepository(
    User,
    config=RepoConfig(apply_soft_delete_filter=False),
)
```
