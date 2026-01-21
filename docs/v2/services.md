# Services (v2)

Services combine repository statements, async execution, and serialization.

## Base services

- `RepositoryService[PKType, ModelType, DetailSchema, ListSchema]`
- `SoftDeleteRepositoryService[PKType, ModelType, DetailSchema, ListSchema]`

`ListSchema` defaults to `DetailSchema` if omitted.

Both include create/update/delete/retrieve/list/paginate helpers.

## Query execution

All v2 service mixins route database operations through `SessionExecutorMixin`.
This gives one consistent execution path for:

- translating integrity errors (unique/FK) into domain exceptions
- standardized execution helpers (`execute`, `execute_scalar_one`, `execute_scalars_all`)

If you are adding new service logic, prefer `self.execute(...)` and
`self.execute_scalars_all(...)` instead of direct `session.execute(...)` calls.

## ServiceConfig

Use `ServiceConfig` to specify default schemas:

```python
from notora.v2.services import RepositoryService, ServiceConfig

service = RepositoryService(repo, config=ServiceConfig(detail_schema=UserSchema))
```

Serialized methods require a schema. If `detail_schema` / `list_schema` are not
configured, pass `schema=...` explicitly or use the `_raw` variants.

## Detail vs list schema

- `detail_schema` is used for single-entity responses (create/retrieve/update).
- `list_schema` is used for list and pagination responses.
- `list_schema` defaults to `detail_schema` when omitted.

You can use `RepositoryServiceD`, `SoftDeleteRepositoryServiceD`, and
`ServiceConfigD` when both schemas are the same.

### Class defaults

You can declare default schemas directly on the service class:

```python
from uuid import UUID

from notora.v2.services import RepositoryService


class UserService(RepositoryService[UUID, User, UserDetailSchema, UserListSchema]):
    detail_schema = UserDetailSchema
    list_schema = UserListSchema
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
- `create`, `update`, `upsert` -> always serialize to schema

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
# Use the raw variants to work with SQLAlchemy models directly.
user_model = await service.create_raw(session, payload)
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
