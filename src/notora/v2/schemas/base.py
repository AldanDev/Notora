from collections.abc import Sequence
from typing import Annotated

from pydantic import BaseModel, ConfigDict, PlainSerializer

from notora.types import AnyIPAddress


class BaseResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class BaseRequestSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PaginationMetaSchema(BaseModel):
    limit: int
    offset: int
    total: int

    @classmethod
    def calculate(cls, total: int, limit: int, offset: int) -> 'PaginationMetaSchema':
        if limit <= 0:
            msg = 'limit must be a positive integer.'
            raise ValueError(msg)
        if offset < 0:
            msg = 'offset must be zero or a positive integer.'
            raise ValueError(msg)
        total_value = max(total, 0)
        return cls(
            limit=limit,
            offset=offset,
            total=total_value,
        )


class PaginatedResponseSchema[T](BaseResponseSchema):
    meta: PaginationMetaSchema
    data: Sequence[T]


class ClientMeta(BaseRequestSchema):
    ip_address: Annotated[AnyIPAddress, PlainSerializer(str, return_type=str)] | None = None
    user_agent: str | None = None
