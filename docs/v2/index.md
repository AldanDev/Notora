# notora v2 documentation

This section describes the v2 toolkit in detail with practical examples for
backend developers (FastAPI-friendly) and library users who want to customize
behavior without adding new dependencies.

## Quickstart

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

## Detailed quickstart

```python
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession

from notora.v2.models.base import AuditedBaseModel
from notora.v2.repositories import Repository
from notora.v2.schemas.base import BaseResponseSchema, BaseRequestSchema
from notora.v2.services import RepositoryService, ServiceConfig


class User(AuditedBaseModel):
    # SQLAlchemy columns
    email: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str]


class UserResponseSchema(BaseResponseSchema):
    # Pydantic response schema
    id: UUID
    email: str
    name: str


class UserCreateSchema(BaseRequestSchema):
    email: str
    name: str


repo = Repository(User)
service = RepositoryService(
    repo,
    config=ServiceConfig(detail_schema=UserResponseSchema),
)


async def create_user(session: AsyncSession, payload: UserCreateSchema, actor_id: UUID) -> UserResponseSchema:
    # actor_id populates updated_by when the model supports it
    return await service.create(session, payload, actor_id=actor_id)


async def list_users(session: AsyncSession) -> list[UserResponseSchema]:
    # schema=None uses the service default schema
    return await service.list(session, limit=50)
```

## Topics

- Models and mixins: `models.md`
- Repositories and configs: `repositories.md`
- Services and `actor_id`: `services.md`
- Query DSL and FastAPI: `query-dsl.md`
- Pagination: `pagination.md`
- M2M sync helpers: `m2m.md`
- Recipes and patterns: `recipes.md`

## Design notes

- v2 is built around mixins and explicit configuration.
- Query filtering and sorting are done via allowlists for safety.
- No extra dependencies are required beyond SQLAlchemy and Pydantic.
