from typing import Any, Protocol

from notora.v2.models.base import GenericBaseModel
from notora.v2.repositories.base import RepositoryProtocol


class _UpdatedByProvider[PKType, ModelType: GenericBaseModel](Protocol):
    repo: RepositoryProtocol[PKType, ModelType]
    updated_by_attribute: str


class UpdatedByServiceMixin[PKType, ModelType: GenericBaseModel]:
    updated_by_attribute: str = 'updated_by'

    def _apply_updated_by(
        self: _UpdatedByProvider[PKType, ModelType],
        payload: dict[str, Any],
        actor_id: Any | None,
    ) -> dict[str, Any]:
        if actor_id is None:
            return payload
        model = self.repo.model
        if not hasattr(model, self.updated_by_attribute):
            msg = (
                f'updated_by field "{self.updated_by_attribute}" is not defined on '
                f'{model.__name__}.'
            )
            raise ValueError(msg)
        if self.updated_by_attribute not in payload:
            payload[self.updated_by_attribute] = actor_id
        return payload
