import re
import uuid
from datetime import datetime
from typing import Any, ClassVar

from sqlalchemy import DateTime, ForeignKey, MetaData, Uuid, func
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    declared_attr,
    mapped_column,
    relationship,
)

POSTGRES_NAMING_CONVENTION = {
    'ix': '%(column_0_label)s_idx',
    'uq': '%(table_name)s_%(column_0_name)s_key',
    'ck': '%(table_name)s_%(constraint_name)s_check',
    'fk': '%(table_name)s_%(column_0_name)s_fkey',
    'pk': '%(table_name)s_pkey',
}
metadata = MetaData(naming_convention=POSTGRES_NAMING_CONVENTION)


class Base(DeclarativeBase):
    metadata = metadata


class CreatableMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
    )


class UpdatableMixin:
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        onupdate=func.now(),
    )


class UpdatedByMixin:
    updated_by_fk_target: ClassVar[str | None] = None
    updated_by_fk_kwargs: ClassVar[dict[str, Any]] = {}

    @declared_attr
    @classmethod
    def updated_by(cls) -> Mapped[uuid.UUID | None]:
        if cls.updated_by_fk_target:
            return mapped_column(
                Uuid,
                ForeignKey(cls.updated_by_fk_target, **cls.updated_by_fk_kwargs),
                nullable=True,
            )
        return mapped_column(Uuid, nullable=True)


class UpdatedByUserMixin(UpdatedByMixin):
    updated_by_fk_target: ClassVar[str | None] = 'user.id'
    updated_by_fk_kwargs: ClassVar[dict[str, Any]] = {'use_alter': True}

    @declared_attr
    @classmethod
    def updated_by_user(cls) -> Mapped[Any | None]:
        return relationship('User', foreign_keys=[cls.updated_by])


class SoftDeletableMixin:
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False),
        nullable=True,
        default=None,
    )


class GenericBaseModel(Base, CreatableMixin):
    __abstract__ = True
    pk_type: ClassVar[Any] = Uuid
    pk_kwargs: ClassVar[dict[str, Any]] = {
        'server_default': func.gen_random_uuid(),
    }

    @declared_attr  # type: ignore[arg-type]
    def __tablename__(cls) -> str:  # noqa: N805
        return re.compile(r'(?<!^)(?=[A-Z])').sub('_', cls.__name__).lower()

    @declared_attr
    @classmethod
    def id(cls) -> Mapped[Any]:
        return mapped_column(cls.pk_type, primary_key=True, **cls.pk_kwargs)

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} id={self.id}>'

    def to_dict(self) -> dict[str, Any]:
        return {field.name: getattr(self, field.name) for field in self.__table__.columns}


class BaseModel(GenericBaseModel, UpdatableMixin, SoftDeletableMixin):
    __abstract__ = True


class UpdatableModel(GenericBaseModel, UpdatableMixin):
    __abstract__ = True


class UpdatedByUserModel(GenericBaseModel, UpdatableMixin, UpdatedByUserMixin):
    __abstract__ = True


class SoftDeletableModel(GenericBaseModel, SoftDeletableMixin):
    __abstract__ = True


class AuditedBaseModel(BaseModel, UpdatedByUserMixin):
    __abstract__ = True
