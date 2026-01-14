from uuid import UUID

from notora.v2.services.base import RepositoryService, SoftDeleteRepositoryService
from notora.v2.services.mixins.m2m import ManyToManyRelation
from tests.v2.test_integration.mocks.model import V2Profile, V2User, V2UserRole
from tests.v2.test_integration.mocks.schema import (
    V2ProfileResponseSchema,
    V2UserResponseSchema,
)


class V2UserService(SoftDeleteRepositoryService[UUID, V2User, V2UserResponseSchema]):
    many_to_many_relations = (
        ManyToManyRelation[V2UserRole](
            payload_field='role_ids',
            association_model=V2UserRole,
            left_key=V2UserRole.user_id,
            right_key=V2UserRole.role_id,
        ),
    )


class V2ProfileService(RepositoryService[UUID, V2Profile, V2ProfileResponseSchema]): ...
