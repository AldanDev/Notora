from typing import Any

from pydantic import BaseModel as PydanticModel

from notora.v2.models.base import GenericBaseModel


class PayloadMixin[ModelType: GenericBaseModel]:
    @staticmethod
    def _dump_payload(
        data: PydanticModel | dict[str, Any],
        *,
        exclude_unset: bool,
    ) -> dict[str, Any]:
        if isinstance(data, dict):
            return dict(data)
        return data.model_dump(exclude_unset=exclude_unset)
