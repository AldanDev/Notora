# Recipes (v2)

## FastAPI list endpoint with query DSL

```python
from fastapi import Depends, FastAPI
from notora.v2.repositories import (
    FilterField,
    SortField,
    make_query_params_dependency,
)

app = FastAPI()

# Allowlist of filterable/sortable fields.
filter_fields = {
    "name": FilterField(resolver=lambda m: m.name, value_type=str),
    "status": FilterField(resolver=lambda m: m.status, value_type=str, operators={"eq", "in"}),
}

sort_fields = {
    "created_at": SortField(resolver=lambda m: m.created_at),
}

# Dependency parses query params into QueryParams.
query_params_dep = make_query_params_dependency(
    model=User,
    filter_fields=filter_fields,
    sort_fields=sort_fields,
)

@app.get("/users")
async def list_users(params = Depends(query_params_dep)):
    # service = RepositoryService(repo)
    # session = AsyncSession(...)
    return await service.list_params(session, params)
```

## Paginated endpoint with total count

```python
from fastapi import FastAPI, Query
from notora.v2.repositories import QueryInput, build_query_params

app = FastAPI()

@app.get("/users/page")
async def list_users_page(
    limit: int = 20,
    offset: int = 0,
    filter_: list[str] = Query(default=[], alias="filter"),
    sort: list[str] = Query(default=[]),
):
    # Parse filters/sorts with the DSL, but keep limit/offset explicit.
    query_input = QueryInput(filter=filter_, sort=sort, limit=limit, offset=offset)
    params = build_query_params(
        query_input,
        model=User,
        filter_fields=filter_fields,
        sort_fields=sort_fields,
    )
    return await service.paginate(
        session,
        filters=params.filters,
        ordering=params.ordering,
        limit=limit,
        offset=offset,
    )
```

## Repository defaults with RepoConfig

```python
from notora.v2.repositories import RepoConfig, Repository

# Defaults apply whenever limit/order are omitted.
repo = Repository(
    User,
    config=RepoConfig(
        default_limit=50,
        default_ordering=(User.created_at.desc(),),
    ),
)
service = RepositoryService(repo)
```

## Upsert with conflict columns

```python
entity = await service.upsert(
    session,
    data={"email": "a@b.com", "name": "Alice"},
    conflict_columns=[User.email],
    update_only=["name"],
    actor_id=current_user_id,
)
```

## Soft delete service

```python
repo = SoftDeleteRepository(User)
service = SoftDeleteRepositoryService(repo)

# Returns the deleted entity as a schema.
deleted = await service.soft_delete(session, user_id)

# Track who performed the deletion (requires UpdatedByMixin on the model).
deleted = await service.soft_delete(session, user_id, actor_id=current_user_id)

# Bulk soft delete by filters — returns a list of deleted schemas.
deleted_list = await service.soft_delete_by(
    session,
    filters=[User.is_active == False],
)

# Raw variants return ORM models instead of schemas.
entity = await service.soft_delete_raw(session, user_id)
entities = await service.soft_delete_by_raw(session, filters=[User.is_active == False])

# Hard delete also returns entities.
deleted = await service.delete(session, user_id)
deleted_list = await service.delete_by(session, filters=[User.is_active == False])

# Customize column name if your model differs.
repo.deleted_attribute = "removed_at"
```

By default, `SoftDeleteRepository` excludes soft-deleted rows. If you need to
include them, disable the filter:

```python
repo = SoftDeleteRepository(
    User,
    config=RepoConfig(apply_soft_delete_filter=False),
)
```

## Actor-aware updates

```python
# Model should include UpdatedByMixin / UpdatedByUserMixin to store actor id.
created = await service.create(session, data, actor_id=current_user_id)
updated = await service.update(session, user_id, data, actor_id=current_user_id)
deleted = await service.soft_delete(session, user_id, actor_id=current_user_id)
```

If your field is not named `updated_by`, override `updated_by_attribute` on the
service.

```python
class UserService(RepositoryService[UUID, User, UserSchema]):
    updated_by_attribute = "updated_by_id"
```

## Filter schema with Annotated metadata (pydantic path)

Single source of truth per field — type and SQL spec live together:

```python
from typing import Annotated, ClassVar
from uuid import UUID

from notora.v2 import Filter, PydanticFiltersSchema


class AdminFooFilters(PydanticFiltersSchema[Foo]):
    name: Annotated[str | None, Filter(resolver=Foo.name)] = None
    age_gte: Annotated[int | None, Filter(resolver=Foo.age, operator='gte')] = None
    owner_id: Annotated[UUID | None, Filter(resolver=Foo.owner_id)] = None
    # Bare pydantic field (no Filter) is skipped at spec-build time —
    # use this for control flags that aren't SQL filters:
    show_archived: bool = False
```

Same `make_list_params_dependency` wiring as the legacy `filter_fields` style:

```python
list_deps = make_list_params_dependency(
    model=Foo,
    filters_schema=AdminFooFilters,
    order_schema=AdminFooOrdering,
)
```

A schema cannot mix `Annotated[..., Filter(...)]` and a `filter_fields: ClassVar[...]` dict — `__pydantic_init_subclass__` raises `TypeError` at class-definition time if it sees both.
