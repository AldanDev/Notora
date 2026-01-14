from uuid import UUID

from notora.v2.schemas.base import BaseRequestSchema, BaseResponseSchema


class V2UserCreateSchema(BaseRequestSchema):
    id: UUID
    email: str
    name: str
    is_active: bool = True


class V2UserResponseSchema(BaseResponseSchema):
    id: UUID
    email: str
    name: str
    is_active: bool
    updated_by: UUID | None = None


class V2ProfileResponseSchema(BaseResponseSchema):
    id: UUID
    user_id: UUID
    bio: str
