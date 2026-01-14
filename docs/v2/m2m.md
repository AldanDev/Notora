# Many-to-many helpers (v2)

The `ManyToManySyncMixin` helps synchronize association tables during
create/update/upsert flows.

## Sync modes

`M2MSyncMode` enum:

- `REPLACE` (default)
- `ADD`
- `REMOVE`

```python
from notora.v2.services import M2MSyncMode

class UserService(RepositoryService[UUID, User, UserSchema]):
    m2m_sync_mode = M2MSyncMode.ADD
```

## Defining relations

```python
from notora.v2.services.mixins.m2m import ManyToManyRelation

class UserService(RepositoryService[UUID, User, UserSchema]):
    many_to_many_relations = (
        ManyToManyRelation[
            UserRole
        ](
            payload_field="role_ids",
            association_model=UserRole,
            left_key=UserRole.user_id,
            right_key=UserRole.role_id,
        ),
    )
```

When the payload contains `role_ids`, the service will sync that association
set according to the configured mode.

## Detailed examples

### Custom row_factory for extra columns

```python
from datetime import datetime
from notora.v2.services.mixins.m2m import ManyToManyRelation

class UserService(RepositoryService[UUID, User, UserSchema]):
    many_to_many_relations = (
        ManyToManyRelation[
            UserRole
        ](
            payload_field="role_ids",
            association_model=UserRole,
            left_key=UserRole.user_id,
            right_key=UserRole.role_id,
            # Include extra fields on the association row.
            row_factory=lambda user_id, role_id: {
                "user_id": user_id,
                "role_id": role_id,
                "created_at": datetime.utcnow(),
            },
        ),
    )
```

### Manual sync for custom flows

```python
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

class UserService(RepositoryService[UUID, User, UserSchema]):
    async def add_roles(
        self,
        session: AsyncSession,
        user_id: UUID,
        role_ids: list[UUID],
    ) -> None:
        # Only add missing relations without removing existing ones.
        await self.sync_m2m_relations(
            session,
            user_id,
            {"role_ids": role_ids},
            mode=M2MSyncMode.ADD,
        )
```

### Remove specific relations

```python
await service.sync_m2m_relations(
    session,
    user_id,
    {"role_ids": [role_to_remove]},
    mode=M2MSyncMode.REMOVE,
)
```
