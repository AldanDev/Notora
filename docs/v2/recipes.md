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

await service.soft_delete(session, user_id)

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
await service.update(session, user_id, data, actor_id=current_user_id)
```

If your field is not named `updated_by`, override `updated_by_attribute` on the
service.

```python
class UserService(RepositoryService[UUID, User, UserSchema]):
    updated_by_attribute = "updated_by_id"
```
