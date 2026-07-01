# Models and mixins (v2)

v2 models are built from small mixins so you only include the fields you need.

## Core base

- `GenericBaseModel` adds:
  - `id` (UUID by default, server default `gen_random_uuid()`)
    - Override via `pk_type` / `pk_kwargs` (`primary_key=True` is applied by default)
  - `created_at` (via `CreatableMixin`)
  - `to_dict()` helper
  - `__tablename__` defaults to snake_case of the class name (override by defining `__tablename__`)
- `Base` uses a shared SQLAlchemy `MetaData` with naming conventions.

## Mixins

- `UpdatableMixin` -> `updated_at`
- `UpdatedByMixin` -> `updated_by` (UUID, nullable)
  - Optional FK via `updated_by_fk_target` / `updated_by_fk_kwargs`
- `UpdatedByUserMixin` -> `updated_by_user` relationship to `User`
  - Configures `updated_by` FK to `user.id`
  - Use only if a `User` model exists in your metadata.
- `SoftDeletableMixin` -> `deleted_at`

## Convenience base classes

- `BaseModel` = `GenericBaseModel + UpdatableMixin + SoftDeletableMixin`
- `UpdatableModel` = `GenericBaseModel + UpdatableMixin`
- `UpdatedByUserModel` = `GenericBaseModel + UpdatableMixin + UpdatedByUserMixin`
- `SoftDeletableModel` = `GenericBaseModel + SoftDeletableMixin`
- `AuditedBaseModel` = `GenericBaseModel + UpdatableMixin + UpdatedByUserMixin + SoftDeletableMixin`

## Example

```python
from sqlalchemy.orm import Mapped, mapped_column
from notora.v2.models.base import AuditedBaseModel

class User(AuditedBaseModel):
    email: Mapped[str] = mapped_column(unique=True)
```

## Notes

- If you want `updated_by` but do not have a `User` model, use `UpdatedByMixin`
  instead of `UpdatedByUserMixin`.
- Services can auto-fill `updated_by` when you pass `actor_id` (see `services.md`).
- If you override `pk_type`, also adjust `pk_kwargs` to match your DB.

## Detailed examples

### Basic model with timestamps only

```python
from sqlalchemy.orm import Mapped, mapped_column
from notora.v2.models.base import GenericBaseModel, UpdatableMixin


class Project(GenericBaseModel, UpdatableMixin):
    name: Mapped[str] = mapped_column(unique=True)
```

### Custom primary key type

```python
from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column
from notora.v2.models.base import GenericBaseModel


class IntPkModel(GenericBaseModel):
    pk_type = Integer
    pk_kwargs = {"autoincrement": True}

    name: Mapped[str] = mapped_column(unique=True)
```

### Audit without a User model

```python
from sqlalchemy.orm import Mapped, mapped_column
from notora.v2.models.base import GenericBaseModel, UpdatableMixin, UpdatedByMixin


class AuditEvent(GenericBaseModel, UpdatableMixin, UpdatedByMixin):
    # updated_by is just a UUID column; no relationship needed
    event: Mapped[str]
```

### Audit with User relationship

```python
from sqlalchemy.orm import Mapped, mapped_column, relationship
from notora.v2.models.base import UpdatedByUserModel, GenericBaseModel


class User(GenericBaseModel):
    email: Mapped[str] = mapped_column(unique=True)


class Task(UpdatedByUserModel):
    title: Mapped[str]
    # updated_by_user relationship is provided by UpdatedByUserModel
```

### Full audit + soft delete in one base

```python
from sqlalchemy.orm import Mapped, mapped_column
from notora.v2.models.base import AuditedBaseModel


class Invoice(AuditedBaseModel):
    number: Mapped[str]
    total: Mapped[int]
```
