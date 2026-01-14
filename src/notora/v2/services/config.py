from dataclasses import dataclass

from notora.v2.schemas.base import BaseResponseSchema


@dataclass(slots=True)
class ServiceConfig[ResponseSchema: BaseResponseSchema]:
    detail_schema: type[ResponseSchema] | None = None
    list_schema: type[ResponseSchema] | None = None
