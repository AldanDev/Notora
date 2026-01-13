from __future__ import annotations

from collections.abc import Iterable
from typing import Literal, Protocol

from notora.persistence.models.base import GenericBaseModel
from notora.schemas.base import BaseResponseSchema


class SerializerProtocol[ModelType: GenericBaseModel](Protocol):
    def serialize_one(
        self,
        obj: ModelType,
        *,
        schema: type[BaseResponseSchema] | Literal[False] | None = None,
    ) -> BaseResponseSchema | ModelType: ...

    def serialize_many(
        self,
        objs: Iterable[ModelType],
        *,
        schema: type[BaseResponseSchema] | Literal[False] | None = None,
        prefer_list_schema: bool = True,
    ) -> list[BaseResponseSchema] | list[ModelType]: ...


class SerializerMixin[ModelType: GenericBaseModel, ResponseSchema: BaseResponseSchema]:
    detail_schema: type[ResponseSchema] | None = None
    list_schema: type[ResponseSchema] | None = None

    def serialize_one(
        self,
        obj: ModelType,
        *,
        schema: type[BaseResponseSchema] | Literal[False] | None = None,
    ) -> BaseResponseSchema | ModelType:
        match schema:
            case False:
                return obj
            case None:
                schema = self.detail_schema
        if schema is None:
            return obj
        return schema.model_validate(obj)

    def serialize_many(
        self,
        objs: Iterable[ModelType],
        *,
        schema: type[BaseResponseSchema] | Literal[False] | None = None,
        prefer_list_schema: bool = True,
    ) -> list[BaseResponseSchema | ModelType]:
        if schema is None and prefer_list_schema:
            schema = self.list_schema or self.detail_schema
        return [self.serialize_one(obj, schema=schema) for obj in objs]
