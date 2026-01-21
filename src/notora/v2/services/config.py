from dataclasses import dataclass

from notora.v2.schemas.base import BaseResponseSchema


@dataclass(slots=True)
class ServiceConfig[
    DetailSchema: BaseResponseSchema,
    ListSchema: BaseResponseSchema = DetailSchema,
]:
    detail_schema: type[DetailSchema] | None = None
    list_schema: type[ListSchema] | None = None


type ServiceConfigD[DetailSchema: BaseResponseSchema] = ServiceConfig[DetailSchema, DetailSchema]
