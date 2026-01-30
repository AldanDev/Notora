from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from notora.v2.models.base import (
    GenericBaseModel,
    SoftDeletableMixin,
    UpdatableMixin,
    UpdatedByMixin,
)


class V2User(GenericBaseModel, UpdatableMixin, UpdatedByMixin, SoftDeletableMixin):
    __table_args__ = (UniqueConstraint('email', name='v2_user_email_key'),)

    email: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class V2Role(GenericBaseModel):
    name: Mapped[str] = mapped_column(String, nullable=False)


class V2UserRole(GenericBaseModel):
    __table_args__ = (UniqueConstraint('user_id', 'role_id', name='v2_user_role_unique'),)

    user_id: Mapped[UUID] = mapped_column(
        PGUUID,
        ForeignKey('v2_user.id', ondelete='CASCADE'),
        nullable=False,
    )
    role_id: Mapped[UUID] = mapped_column(
        PGUUID,
        ForeignKey('v2_role.id', ondelete='CASCADE'),
        nullable=False,
    )


class V2Profile(GenericBaseModel):
    user_id: Mapped[UUID] = mapped_column(
        PGUUID,
        ForeignKey('v2_user.id'),
        nullable=False,
    )
    bio: Mapped[str] = mapped_column(String, nullable=False)
