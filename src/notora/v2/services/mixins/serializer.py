from collections.abc import Iterable
from typing import Protocol

from notora.v2.models.base import GenericBaseModel
from notora.v2.schemas.base import BaseResponseSchema


class SerializerProtocol[ModelType: GenericBaseModel](Protocol):
    def serialize_one(
        self,
        obj: ModelType,
        *,
        schema: type[BaseResponseSchema] | None = None,
    ) -> BaseResponseSchema: ...

    def serialize_many(
        self,
        objs: Iterable[ModelType],
        *,
        schema: type[BaseResponseSchema] | None = None,
        prefer_list_schema: bool = True,
    ) -> list[BaseResponseSchema]: ...


class SerializerMixin[ModelType: GenericBaseModel, ResponseSchema: BaseResponseSchema]:
    detail_schema: type[ResponseSchema] | None = None
    list_schema: type[ResponseSchema] | None = None

    def serialize_one(
        self,
        obj: ModelType,
        *,
        schema: type[BaseResponseSchema] | None = None,
    ) -> BaseResponseSchema:
        if schema is None:
            schema = self.detail_schema
        if schema is None:
            msg = 'schema is required for serialized methods; use *_raw or set detail_schema.'
            raise ValueError(msg)
        return schema.model_validate(obj)

    def serialize_many(
        self,
        objs: Iterable[ModelType],
        *,
        schema: type[BaseResponseSchema] | None = None,
        prefer_list_schema: bool = True,
    ) -> list[BaseResponseSchema]:
        if schema is None and prefer_list_schema:
            schema = self.list_schema or self.detail_schema
        if schema is None:
            msg = 'schema is required for serialized methods; use *_raw or set list_schema.'
            raise ValueError(msg)
        return [schema.model_validate(obj) for obj in objs]
