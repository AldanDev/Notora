import re
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, MetaData, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    declared_attr,
    mapped_column,
    relationship,
)
from sqlalchemy.sql.functions import GenericFunction

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


class GenerateUUID(GenericFunction[uuid.UUID]):
    type = UUID()
    name = 'gen_random_uuid'
    identifier = 'gen_random_uuid'


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

    @declared_attr
    @classmethod
    def updated_by(cls) -> Mapped[uuid.UUID | None]:
        return mapped_column(ForeignKey('user.id', use_alter=True))

    @declared_attr
    @classmethod
    def updated_by_user(cls) -> Mapped[uuid.UUID | None]:
        return relationship('User', foreign_keys=[cls.updated_by])


class SoftDeletableMixin:
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False),
        nullable=True,
        default=None,
    )


class GenericBaseModel(Base, CreatableMixin):
    __abstract__ = True
    id: Mapped[uuid.UUID] = mapped_column(
        UUID,
        primary_key=True,
        server_default=GenerateUUID(),
    )

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} id={self.id}>'

    def to_dict(self) -> dict[str, Any]:
        return {field.name: getattr(self, field.name) for field in self.__table__.columns}


class BaseModel(GenericBaseModel, UpdatableMixin, SoftDeletableMixin):
    __abstract__ = True

    @declared_attr  # type: ignore[arg-type]
    def __tablename__(cls) -> str:  # noqa: N805
        return re.compile(r'(?<!^)(?=[A-Z])').sub('_', cls.__name__).lower()


class UpdatableModel(GenericBaseModel, UpdatableMixin):
    __abstract__ = True


class SoftDeletableModel(GenericBaseModel, SoftDeletableMixin):
    __abstract__ = True
