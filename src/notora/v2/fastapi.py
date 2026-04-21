from collections.abc import Callable

from notora.v2.models.base import GenericBaseModel
from notora.v2.repositories.params import PaginationParams
from notora.v2.schemas.query import PydanticFiltersSchema, PydanticOrderBySchema

__all__ = ['make_admin_list_params_dep']


def make_admin_list_params_dep[ModelType: GenericBaseModel](
    *,
    model: type[ModelType],
    filters_schema: type[PydanticFiltersSchema[ModelType]],
    order_schema: type[PydanticOrderBySchema[ModelType]],
    default_limit: int = 20,
) -> Callable[..., PaginationParams[ModelType]]:
    try:
        fastapi = __import__('fastapi')
    except Exception as exc:  # pragma: no cover - only used in FastAPI apps
        msg = 'fastapi is required to use make_admin_list_params_dep.'
        raise RuntimeError(msg) from exc

    filters_dep = fastapi.Depends()
    ordering_dep = fastapi.Depends()
    limit_query = fastapi.Query(default_limit, ge=1)
    offset_query = fastapi.Query(0, ge=0)

    def _dependency(
        filters: filters_schema = filters_dep,  # type: ignore[valid-type]
        ordering: order_schema = ordering_dep,  # type: ignore[valid-type]
        limit: int = limit_query,
        offset: int = offset_query,
        *,
        apply_default_filters: bool = True,
    ) -> PaginationParams[ModelType]:
        return PaginationParams(
            filters=filters.build_filter_specs(model),  # type: ignore[attr-defined]
            ordering=ordering.build_ordering(model),  # type: ignore[attr-defined]
            limit=limit,
            offset=offset,
            apply_default_filters=apply_default_filters,
        )

    return _dependency
