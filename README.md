[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/notora)](https://badge.fury.io/py/notora)
[![PyPI version](https://badge.fury.io/py/notora.svg)](https://badge.fury.io/py/notora)

## notora

Shared base logic used across AldanDev projects.

- v1 (legacy): `notora.v1`
- v2 (next-gen toolkit): `notora.v2`

## v2 quickstart

```python
from notora.v2.repositories import Repository, RepoConfig
from notora.v2.services import RepositoryService, ServiceConfig

repo = Repository(
    User,
    config=RepoConfig(default_limit=50),
)
service = RepositoryService(
    repo,
    config=ServiceConfig(detail_schema=UserSchema, list_schema=UserListSchema),
)
```

## v2 docs

- `docs/v2/index.md`
- `docs/v2/models.md`
- `docs/v2/repositories.md`
- `docs/v2/services.md`
- `docs/v2/query-dsl.md`
- `docs/v2/pagination.md`
- `docs/v2/m2m.md`
- `docs/v2/recipes.md`

### Listing and pagination

```python
from notora.v2.repositories import QueryParams, PaginationParams

rows = await service.list_raw(
    session,
    limit=None,  # no limit
)

params = QueryParams(filters=[...], ordering=[...], limit=None)
rows = await service.list_raw_params(session, params)

page = await service.paginate_params(
    session,
    PaginationParams(limit=20, offset=0, filters=[...]),
)
```

### Repository/service factories

```python
from notora.v2.repositories import build_repository, RepoConfig
from notora.v2.services import build_service, ServiceConfig

repo = build_repository(User, config=RepoConfig(default_limit=25))
service = build_service(User, repo=repo, service_config=ServiceConfig(detail_schema=UserSchema))
```

### Query DSL (FastAPI-friendly)

```python
from fastapi import Depends
from notora.v2.repositories import (
    FilterField,
    QueryParams,
    QueryInput,
    SortField,
    build_query_params,
    make_query_params_dependency,
)

filter_fields = {
    'name': FilterField(resolver=lambda m: m.name, value_type=str),
    'age': FilterField(resolver=lambda m: m.age, value_type=int, operators={'eq', 'gte', 'lte'}),
}
sort_fields = {
    'name': SortField(resolver=lambda m: m.name),
    'created_at': SortField(resolver=lambda m: m.created_at),
}

def query_params(query: QueryInput = Depends()) -> QueryParams[User]:
    return build_query_params(
        query,
        model=User,
        filter_fields=filter_fields,
        sort_fields=sort_fields,
    )

query_params_dep = make_query_params_dependency(
    model=User,
    filter_fields=filter_fields,
    sort_fields=sort_fields,
)

# Example request:
# /users?filter=name:eq:john&filter=age:gte:18&sort=-created_at&limit=20&offset=0
```

Supported operators: `eq`, `ne`, `lt`, `lte`, `gt`, `gte`, `in`, `ilike`, `isnull`.

### M2M sync modes

```python
from notora.v2.services import M2MSyncMode

class UserService(RepositoryService[UUID, User, UserSchema]):
    m2m_sync_mode: M2MSyncMode = M2MSyncMode.ADD
```
