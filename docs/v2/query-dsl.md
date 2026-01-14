# Query DSL (v2)

The v2 query DSL converts FastAPI query parameters into `QueryParams` without
extra dependencies. It uses allowlists to keep filtering and sorting safe.

## Input format

Filters (repeatable):

- `filter=field:op:value`

Sorting (repeatable):

- `sort=-field` (descending)
- `sort=+field` or `sort=field` (ascending)

Example:

```
/users?filter=name:eq:john&filter=age:gte:18&sort=-created_at&limit=20&offset=0
```

Supported operators:

- `eq`, `ne`, `lt`, `lte`, `gt`, `gte`, `in`, `ilike`, `isnull`

Notes:
- `in` values are comma-separated: `status:in:active,blocked`.
- `isnull` accepts `true`/`false`. If value is omitted it defaults to `true`.
- `:` and `,` must be URL-encoded if they appear in values.

## Allowlist fields

You must provide maps for filters and sorting:

```python
from notora.v2.repositories import FilterField, SortField

filter_fields = {
    "name": FilterField(resolver=lambda m: m.name, value_type=str),
    "age": FilterField(resolver=lambda m: m.age, value_type=int, operators={"eq", "gte"}),
}

sort_fields = {
    "name": SortField(resolver=lambda m: m.name),
    "created_at": SortField(resolver=lambda m: m.created_at),
}
```

Resolvers can be:
- an instrumented attribute
- a SQLAlchemy column expression
- a callable that receives the model and returns a column

For relations, use a callable to build the clause.

Direct attributes work too (no lambda):

```python
filter_fields = {
    "status": FilterField(resolver=User.status, value_type=str),
    "is_active": FilterField(resolver=User.is_active, value_type=bool),
}

sort_fields = {
    "created_at": SortField(resolver=User.created_at),
}
```

## Building QueryParams

```python
from notora.v2.repositories import QueryInput, build_query_params

params = build_query_params(
    QueryInput(filter=["name:eq:john"], sort=["-created_at"], limit=20, offset=0),
    model=User,
    filter_fields=filter_fields,
    sort_fields=sort_fields,
)
```

`limit` handling:
- If omitted, the repository default limit is used.
- For "no limit", bypass the DSL and call `list_raw(limit=None)` or construct
  `QueryParams(limit=None)` directly.

## FastAPI helper dependency

```python
from notora.v2.repositories import make_query_params_dependency

query_params_dep = make_query_params_dependency(
    model=User,
    filter_fields=filter_fields,
    sort_fields=sort_fields,
)

@app.get("/users")
async def list_users(params = Depends(query_params_dep)):
    return await service.list_params(session, params)
```

This helper uses `fastapi.Depends()` internally and returns a dependency
callable that produces `QueryParams`.

## Detailed examples

### IN and ISNULL

```
/users?filter=status:in:active,blocked&filter=deleted_at:isnull:true
```

### Type conversion with value_type

```python
from uuid import UUID
from notora.v2.repositories import FilterField

filter_fields = {
    "id": FilterField(resolver=lambda m: m.id, value_type=UUID),
}
```

### Search across multiple fields

```python
from sqlalchemy import or_
from notora.v2.repositories import FilterField

def search_predicate(model, op, value):
    # Restrict operator to ilike for clarity
    if op != "ilike":
        raise ValueError("Only ilike is supported for search")
    pattern = f"%{value}%"
    return or_(model.name.ilike(pattern), model.email.ilike(pattern))

filter_fields = {
    "q": FilterField(predicate=search_predicate, operators={"ilike"}, value_type=str),
}
```

### FastAPI endpoint example

```python
from fastapi import Depends, FastAPI
from notora.v2.repositories import make_query_params_dependency

app = FastAPI()

query_params_dep = make_query_params_dependency(
    model=User,
    filter_fields=filter_fields,
    sort_fields=sort_fields,
)

@app.get("/users")
async def list_users(params = Depends(query_params_dep)):
    return await service.list_params(session, params)
```
