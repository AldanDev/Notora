from notora.schemas.base import PaginationMetaSchema


def calculate_pagination(*, total: int, limit: int, offset: int) -> PaginationMetaSchema:
    return PaginationMetaSchema.calculate(total=total, limit=limit, offset=offset)
