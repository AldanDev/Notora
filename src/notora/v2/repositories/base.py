from notora.v2.models.base import GenericBaseModel

from .mixins import (
    CountableMixin,
    CreatableMixin,
    DeleteMixin,
    RetrievableMixin,
    SoftDeleteMixin,
    UpdateMixin,
    UpsertableMixin,
    UpsertOrSkipMixin,
)


class Repository[PKType, ModelType: GenericBaseModel](
    RetrievableMixin[PKType, ModelType],
    CreatableMixin[ModelType],
    UpsertableMixin[PKType, ModelType],
    UpsertOrSkipMixin[ModelType],
    UpdateMixin[PKType, ModelType],
    DeleteMixin[PKType, ModelType],
    CountableMixin[ModelType],
):
    """Composition-friendly base repository built out of mixins."""

    def __init__(self, model: type[ModelType], *, default_limit: int = 50) -> None:
        self.model = model
        self.default_limit = default_limit


class SoftDeleteRepository[PKType, ModelType: GenericBaseModel](
    RetrievableMixin[PKType, ModelType],
    CreatableMixin[ModelType],
    UpsertableMixin[PKType, ModelType],
    UpsertOrSkipMixin[ModelType],
    SoftDeleteMixin[PKType, ModelType],
    DeleteMixin[PKType, ModelType],
    CountableMixin[ModelType],
):
    """Repository variant with soft-delete helpers."""

    def __init__(self, model: type[ModelType], *, default_limit: int = 50) -> None:
        self.model = model
        self.default_limit = default_limit
