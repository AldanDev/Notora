# Pagination (v2)

Pagination responses include a meta object with three fields:

- `limit`
- `offset`
- `total`

Example:

```python
page = await service.paginate(session, limit=20, offset=0)
print(page.meta.limit, page.meta.offset, page.meta.total)
```

`PaginationMetaSchema.calculate(total, limit, offset)` validates:
- `limit` must be positive
- `offset` must be zero or positive
- `total` is clamped to a minimum of 0

## No limit vs default

- Use `limit=None` with `list_raw` / `QueryParams` to fetch all rows.
- If `limit` is omitted, the repository default limit is applied.

## Detailed examples

### Basic paginate call

```python
# Paginate returns PaginatedResponseSchema with .data and .meta
page = await service.paginate(
    session,
    limit=25,
    offset=50,
    schema=UserSchema,
)

# data is already serialized when schema is provided
print(len(page.data))
print(page.meta.total)
```

### Custom count query (joins or complex filters)

```python
from sqlalchemy import func, select

limit = 20
offset = 0

data_query = (
    select(User)
    .join(User.roles)
    .where(Role.name == "admin")
    .limit(limit)
    .offset(offset)
)

count_query = (
    select(func.count())
    .select_from(User)
    .join(User.roles)
    .where(Role.name == "admin")
)

page = await service.paginate_from_queries(
    session,
    data_query=data_query,
    count_query=count_query,
    limit=limit,
    offset=offset,
)
```

### Export without a limit

```python
# Pagination requires a positive limit, so exports use list_raw instead.
rows = await service.list_raw(
    session,
    limit=None,
    ordering=[User.created_at],
)
```
