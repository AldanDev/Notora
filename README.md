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

### M2M sync modes

```python
from notora.v2.services import M2MSyncMode

class UserService(RepositoryService[UUID, User, UserSchema]):
    m2m_sync_mode: M2MSyncMode = 'add'
```
