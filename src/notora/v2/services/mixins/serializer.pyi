from collections.abc import Iterable
from typing import Protocol, overload

from notora.v2.models.base import GenericBaseModel
from notora.v2.schemas.base import BaseResponseSchema

__all__ = ['SerializerMixin', 'SerializerProtocol']

class SerializerProtocol[
    ModelType: GenericBaseModel,
    DetailSchema: BaseResponseSchema,
    ListSchema: BaseResponseSchema = DetailSchema,
](Protocol):
    __type_params__: tuple[object, ...]

    @overload
    def serialize_one(
        self,
        obj: ModelType,
        *,
        schema: None = ...,
    ) -> DetailSchema: ...
    @overload
    def serialize_one[SchemaT: BaseResponseSchema](
        self,
        obj: ModelType,
        *,
        schema: type[SchemaT],
    ) -> SchemaT: ...
    @overload
    def serialize_many(
        self,
        objs: Iterable[ModelType],
        *,
        schema: None = ...,
        prefer_list_schema: bool = True,
    ) -> list[ListSchema]: ...
    @overload
    def serialize_many[SchemaT: BaseResponseSchema](
        self,
        objs: Iterable[ModelType],
        *,
        schema: type[SchemaT],
        prefer_list_schema: bool = True,
    ) -> list[SchemaT]: ...

class SerializerMixin[
    ModelType: GenericBaseModel,
    DetailSchema: BaseResponseSchema,
    ListSchema: BaseResponseSchema = DetailSchema,
]:
    __type_params__: tuple[object, ...]
    detail_schema: type[DetailSchema] | None
    list_schema: type[ListSchema] | None

    @overload
    def serialize_one(
        self,
        obj: ModelType,
        *,
        schema: None = ...,
    ) -> DetailSchema: ...
    @overload
    def serialize_one[SchemaT: BaseResponseSchema](
        self,
        obj: ModelType,
        *,
        schema: type[SchemaT],
    ) -> SchemaT: ...
    @overload
    def serialize_many(
        self,
        objs: Iterable[ModelType],
        *,
        schema: None = ...,
        prefer_list_schema: bool = True,
    ) -> list[ListSchema]: ...
    @overload
    def serialize_many[SchemaT: BaseResponseSchema](
        self,
        objs: Iterable[ModelType],
        *,
        schema: type[SchemaT],
        prefer_list_schema: bool = True,
    ) -> list[SchemaT]: ...
