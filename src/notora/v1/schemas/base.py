import typing
from collections.abc import Sequence
from datetime import UTC, datetime
from math import ceil
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import AfterValidator, BaseModel, ConfigDict, PlainSerializer

from notora.types import AnyIPAddress
from notora.v1.enums.base import OrderByDirections


def normalize_datetime_to_utc(dec_value: datetime) -> datetime:
    if dec_value.tzinfo is None or dec_value.utcoffset() is None:
        return dec_value.replace(tzinfo=UTC)
    return dec_value.astimezone(UTC)


def utc_datetime_encoder(dec_value: datetime) -> str:
    return normalize_datetime_to_utc(dec_value).isoformat().replace('+00:00', 'Z')


def datetime_encoder(dec_value: datetime) -> float:
    return normalize_datetime_to_utc(dec_value).timestamp()


utc_datetime = Annotated[
    datetime,
    AfterValidator(normalize_datetime_to_utc),
    PlainSerializer(utc_datetime_encoder, return_type=str, when_used='json'),
]


timestamp = Annotated[
    datetime,
    AfterValidator(normalize_datetime_to_utc),
    PlainSerializer(datetime_encoder, return_type=float),
]


class BaseResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class BaseRequestSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CreateUpdateMeta(BaseModel):
    created_at: utc_datetime
    updated_at: utc_datetime


class AdminMeta(CreateUpdateMeta):
    deleted_at: utc_datetime | None = None


class SetUpdatedBySchema(BaseRequestSchema):
    updated_at: datetime
    updated_by: UUID


class PaginationMetaSchema(BaseModel):
    limit: int
    total: int
    current_page: int
    last_page: int

    @classmethod
    def calculate(cls, total: int, limit: int, offset: int) -> 'PaginationMetaSchema':
        current_page = (offset // limit) + 1 if total >= limit else 1
        last_page = ceil(total / limit) if total > 0 else 1
        return cls(
            limit=limit,
            total=total,
            current_page=current_page,
            last_page=last_page,
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
    exp: utc_datetime
    iat: utc_datetime

    @property
    def id(self) -> UUID:
        return self.sub


class BaseTokenParamsSchema(BaseRequestSchema): ...
