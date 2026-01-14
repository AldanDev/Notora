from uuid import UUID

from notora.v2.repositories.base import Repository, SoftDeleteRepository
from tests.v2.test_integration.mocks.model import V2Profile, V2Role, V2User, V2UserRole


class V2UserRepo(SoftDeleteRepository[UUID, V2User]): ...


class V2RoleRepo(Repository[UUID, V2Role]): ...


class V2UserRoleRepo(Repository[UUID, V2UserRole]): ...


class V2ProfileRepo(Repository[UUID, V2Profile]): ...
