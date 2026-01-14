"""Service mixins and helpers for v2."""

from notora.v2.services.base import RepositoryService, SoftDeleteRepositoryService
from notora.v2.services.config import ServiceConfig
from notora.v2.services.factory import build_service, build_service_for_repo
from notora.v2.services.mixins import (
    CreateOrSkipServiceMixin,
    CreateServiceMixin,
    DeleteServiceMixin,
    ListingServiceMixin,
    M2MSyncMode,
    ManyToManyRelation,
    ManyToManySyncMixin,
    PaginationServiceMixin,
    PayloadMixin,
    RepositoryAccessorMixin,
    RetrievalServiceMixin,
    SerializerMixin,
    SerializerProtocol,
    SessionExecutorMixin,
    SoftDeleteServiceMixin,
    UpdateByFilterServiceMixin,
    UpdatedByServiceMixin,
    UpdateServiceMixin,
    UpsertServiceMixin,
)

__all__ = [
    'CreateOrSkipServiceMixin',
    'CreateServiceMixin',
    'DeleteServiceMixin',
    'ListingServiceMixin',
    'M2MSyncMode',
    'ManyToManyRelation',
    'ManyToManySyncMixin',
    'PaginationServiceMixin',
    'PayloadMixin',
    'RepositoryAccessorMixin',
    'RepositoryService',
    'RetrievalServiceMixin',
    'SerializerMixin',
    'SerializerProtocol',
    'ServiceConfig',
    'SessionExecutorMixin',
    'SoftDeleteRepositoryService',
    'SoftDeleteServiceMixin',
    'UpdateByFilterServiceMixin',
    'UpdateServiceMixin',
    'UpdatedByServiceMixin',
    'UpsertServiceMixin',
    'build_service',
    'build_service_for_repo',
]
