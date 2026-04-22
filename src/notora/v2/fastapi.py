from collections.abc import Callable

from notora.v2.models.base import GenericBaseModel
from notora.v2.repositories.params import PaginationParams
from notora.v2.schemas.query import PydanticFiltersSchema, PydanticOrderBySchema

__all__ = ['make_list_params_dependency']


def make_list_params_dependency[ModelType: GenericBaseModel](
    *,
    model: type[ModelType],
    filters_schema: type[PydanticFiltersSchema[ModelType]],
    order_schema: type[PydanticOrderBySchema[ModelType]],
    default_limit: int = 20,
    max_limit: int | None = 200,
    default_filter_bypass_param: str | None = None,
) -> Callable[..., PaginationParams[ModelType]]:
    """Build a FastAPI dependency that produces a ``PaginationParams`` from request query params.

    The returned callable parses ``filters`` and ``ordering`` via the supplied pydantic
    schemas and exposes ``limit``/``offset`` query parameters. Both schemas are pulled in
    through nested ``Depends()`` — FastAPI flattens their fields into the HTTP query string.

    Args:
        model: SQLAlchemy model class the filter/order specs resolve against.
        filters_schema: Pydantic schema describing the allowed filter fields.
        order_schema: Pydantic schema describing the allowed sort fields.
        default_limit: Default ``limit`` when the client omits it. Must be ``>= 1``.
        max_limit: Upper bound for the ``limit`` query param. ``None`` disables the cap
            (use with care — unbounded ``?limit=1000000`` is a real foot-gun for admin UIs).
            Defaults to ``200``.
        default_filter_bypass_param: When set to a string (e.g. ``'show_deleted'``), the
            returned dependency accepts a public query parameter with that name. A truthy
            value flips ``PaginationParams.apply_default_filters`` to ``False``, letting
            the caller see rows that default filters (soft-delete, etc.) would normally
            hide. When ``None`` (default), no such parameter is exposed and
            ``apply_default_filters`` always stays ``True``.

    Returns:
        A callable suitable for use as a FastAPI dependency; when invoked it returns a
        ``PaginationParams[ModelType]``.

    """
    try:
        fastapi = __import__('fastapi')
    except Exception as exc:  # pragma: no cover - only used in FastAPI apps
        msg = 'fastapi is required to use make_list_params_dependency.'
        raise RuntimeError(msg) from exc

    # FastAPI resolves each sub-dependency by reading its parameter's type annotation,
    # so `Depends()` (no target) is correct here — the target is inferred from
    # `filters: filters_schema` / `ordering: order_schema` below.
    filters_dep = fastapi.Depends()
    ordering_dep = fastapi.Depends()

    if max_limit is None:
        limit_query = fastapi.Query(default_limit, ge=1)
    else:
        limit_query = fastapi.Query(default_limit, ge=1, le=max_limit)
    offset_query = fastapi.Query(0, ge=0)

    if default_filter_bypass_param is None:

        def _dependency(
            filters: filters_schema = filters_dep,  # type: ignore[valid-type]
            ordering: order_schema = ordering_dep,  # type: ignore[valid-type]
            limit: int = limit_query,
            offset: int = offset_query,
        ) -> PaginationParams[ModelType]:
            return PaginationParams(
                filters=filters.build_filter_specs(model),  # type: ignore[attr-defined]
                ordering=ordering.build_ordering(model),  # type: ignore[attr-defined]
                limit=limit,
                offset=offset,
            )

        return _dependency

    bypass_query = fastapi.Query(False, alias=default_filter_bypass_param)  # noqa: FBT003

    def _dependency_with_bypass(
        filters: filters_schema = filters_dep,  # type: ignore[valid-type]
        ordering: order_schema = ordering_dep,  # type: ignore[valid-type]
        limit: int = limit_query,
        offset: int = offset_query,
        bypass_default_filters: bool = bypass_query,  # noqa: FBT001  (FastAPI requires bool annotation for query parsing)
    ) -> PaginationParams[ModelType]:
        return PaginationParams(
            filters=filters.build_filter_specs(model),  # type: ignore[attr-defined]
            ordering=ordering.build_ordering(model),  # type: ignore[attr-defined]
            limit=limit,
            offset=offset,
            apply_default_filters=not bypass_default_filters,
        )

    return _dependency_with_bypass
