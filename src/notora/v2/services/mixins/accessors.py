from notora.v2.models.base import GenericBaseModel

from ...repositories.base import RepositoryProtocol


class RepositoryAccessorMixin[PKType, ModelType: GenericBaseModel]:
    repo: RepositoryProtocol[PKType, ModelType]

    def _extract_pk(self, entity: ModelType) -> PKType:
        pk_attr = getattr(self.repo, 'pk_attribute', 'id')
        return getattr(entity, pk_attr)
