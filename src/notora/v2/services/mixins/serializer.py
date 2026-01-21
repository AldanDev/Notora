from collections.abc import Iterable
from typing import Protocol, cast

from notora.v2.models.base import GenericBaseModel
from notora.v2.schemas.base import BaseResponseSchema

__all__ = ['SerializerMixin', 'SerializerProtocol']


class SerializerProtocol[
    ModelType: GenericBaseModel,
    DetailSchema: BaseResponseSchema,
    ListSchema: BaseResponseSchema = DetailSchema,
](Protocol):
    def serialize_one(
        self,
        obj: ModelType,
        *,
        schema: type[DetailSchema] | None = None,
    ) -> DetailSchema: ...

    def serialize_many(
        self,
        objs: Iterable[ModelType],
        *,
        schema: type[ListSchema] | None = None,
        prefer_list_schema: bool = True,
    ) -> list[ListSchema]: ...


class SerializerMixin[
    ModelType: GenericBaseModel,
    DetailSchema: BaseResponseSchema,
    ListSchema: BaseResponseSchema = DetailSchema,
]:
    detail_schema: type[DetailSchema] | None = None
    list_schema: type[ListSchema] | None = None

    def serialize_one(
        self,
        obj: ModelType,
        *,
        schema: type[DetailSchema] | None = None,
    ) -> DetailSchema:
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
        schema: type[ListSchema] | None = None,
        prefer_list_schema: bool = True,
    ) -> list[ListSchema]:
        if schema is None and prefer_list_schema:
            schema = self.list_schema
            if schema is None:
                schema = cast(type[ListSchema] | None, self.detail_schema)
        if schema is None:
            msg = 'schema is required for serialized methods; use *_raw or set list_schema.'
            raise ValueError(msg)
        return [schema.model_validate(obj) for obj in objs]
