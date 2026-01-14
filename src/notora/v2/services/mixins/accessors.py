from typing import cast

from notora.v2.models.base import GenericBaseModel
from notora.v2.repositories.base import RepositoryProtocol


class RepositoryAccessorMixin[PKType, ModelType: GenericBaseModel]:
    repo: RepositoryProtocol[PKType, ModelType]

    def _extract_pk(self, entity: ModelType) -> PKType:
        pk_attr = getattr(self.repo, 'pk_attribute', 'id')
        return cast(PKType, getattr(entity, pk_attr))
