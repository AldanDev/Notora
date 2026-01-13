from uuid import UUID

from notora.schemas.base import BaseRequestSchema, BaseResponseSchema


class MockModelResponseSchema(BaseResponseSchema):
    id: UUID
    name: str


class CreateMockModelRequestSchema(BaseRequestSchema):
    name: str


class UpdateMockModelRequestSchema(CreateMockModelRequestSchema): ...
