# Services (v2)

Services combine repository statements, async execution, and serialization.

## Base services

- `RepositoryService[PKType, ModelType, ResponseSchema]`
- `SoftDeleteRepositoryService[PKType, ModelType, ResponseSchema]`

Both include create/update/delete/retrieve/list/paginate helpers.

## ServiceConfig

Use `ServiceConfig` to specify default schemas:

```python
from notora.v2.services import RepositoryService, ServiceConfig

service = RepositoryService(repo, config=ServiceConfig(detail_schema=UserSchema))
```

## Actor-aware writes (updated_by)

Write methods accept `actor_id` and will populate `updated_by` when:
- you pass `actor_id`, and
- the model has the `updated_by` field.

This is implemented via `UpdatedByServiceMixin`.

```python
await service.update(session, user_id, data, actor_id=current_user_id)
```

If your model uses a different field name, override it:

```python
class UserService(RepositoryService[UUID, User, UserSchema]):
    updated_by_attribute = "updated_by_id"
```

If `actor_id` is provided and the model does not have the field, a
`ValueError` is raised to avoid silent bugs.

## Raw vs serialized

Each operation has a raw and serialized variant:

- `create_raw`, `update_raw`, `upsert_raw` -> return SQLAlchemy model
- `create`, `update`, `upsert` -> serialize to schema (or raw when `schema=False`)

## Pagination

`paginate` and `paginate_params` return `PaginatedResponseSchema` with meta
containing `limit`, `offset`, and `total`.

## Detailed examples

### Create and serialize

```python
from notora.v2.schemas.base import BaseRequestSchema


class UserCreateSchema(BaseRequestSchema):
    email: str
    name: str


payload = UserCreateSchema(email="a@b.com", name="Alice")
user_schema = await service.create(session, payload)
```

### Raw model response

```python
# schema=False returns the SQLAlchemy model instead of a schema
user_model = await service.create(session, payload, schema=False)
```

### Actor-aware update (updated_by)

```python
updated = await service.update(
    session,
    user_id,
    {"name": "New Name"},
    actor_id=current_user_id,
)
```

### Update by filters

```python
updated = await service.update_by(
    session,
    filters=[lambda m: m.email == "a@b.com"],
    data={"status": "blocked"},
)
```

### Update by filters without lambda

```python
updated = await service.update_by(
    session,
    filters=[User.email == "a@b.com"],
    data={"status": "blocked"},
)
```

### Create or skip

```python
created = await service.create_or_skip(
    session,
    {"email": "a@b.com", "name": "Alice"},
    conflict_columns=[User.email],
)
```

### Upsert

```python
entity = await service.upsert(
    session,
    {"email": "a@b.com", "name": "Alice"},
    conflict_columns=[User.email],
)
```

### List and paginate

```python
rows = await service.list(session, limit=20, offset=0)
page = await service.paginate(session, limit=20, offset=0)
```
