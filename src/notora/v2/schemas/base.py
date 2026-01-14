import typing
from collections.abc import Sequence
from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, PlainSerializer

from notora.types import AnyIPAddress
from notora.v2.enums.base import OrderByDirections


def datetime_encoder(dec_value: datetime) -> float:
    return dec_value.timestamp()


timestamp = Annotated[datetime, PlainSerializer(datetime_encoder, return_type=float)]


class BaseResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class BaseRequestSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CreateUpdateMeta(BaseModel):
    created_at: datetime
    updated_at: datetime


class AdminMeta(CreateUpdateMeta):
    deleted_at: datetime | None = None


class AdminResponseSchema(BaseResponseSchema):
    id: UUID
    full_name: str | None = None
    unovay_name: str | None = None


class PersonalizedAdminMeta(CreateUpdateMeta):
    updated_by_user: AdminResponseSchema | None = None


class SetUpdatedBySchema(BaseRequestSchema):
    updated_at: datetime
    updated_by: UUID


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


class OrderBy(BaseModel):
    field: str
    direction: OrderByDirections = OrderByDirections.ASC
    model: type[Any] | None = None


FilterOp = Literal[
    'eq', '=', 'ilike', '~=', 'is', 'is_not', 'in', 'gt', '>', 'ge', '>=', 'lt', '<', 'le', '<='
]
filter_op_values = typing.get_args(FilterOp)


class Filter(BaseModel):
    field: str
    op: FilterOp = '='
    value: Any | None
    model: type[Any] | None = None


class OrFilterGroup(BaseModel):
    filters: list[Filter]


class BaseTokenSchema(BaseResponseSchema):
    sub: UUID
    iss: str
    nbf: timestamp
    exp: datetime
    iat: datetime

    @property
    def id(self) -> UUID:
        return self.sub


class BaseTokenParamsSchema(BaseRequestSchema): ...
