from collections.abc import Sequence
from dataclasses import dataclass

from notora.v2.models.base import GenericBaseModel
from notora.v2.repositories.types import FilterSpec, OptionSpec, OrderSpec


@dataclass(slots=True)
class RepoConfig[ModelType: GenericBaseModel]:
    default_limit: int | None = None
    default_options: Sequence[OptionSpec[ModelType]] | None = None
    default_filters: Sequence[FilterSpec[ModelType]] | None = None
    default_ordering: Sequence[OrderSpec[ModelType]] | None = None
    fallback_sort_attribute: str | None = None
    pk_attribute: str | None = None
    apply_soft_delete_filter: bool | None = None
