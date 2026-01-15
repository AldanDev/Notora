from collections.abc import Iterable, Sequence
from typing import (
    Any,
    Protocol,
    cast,
    overload,
    override,
)

from sqlalchemy import (
    ScalarSelect,
    Select,
    UnaryExpression,
    and_,
    asc,
    delete,
    desc,
    false,
    func,
    null,
    or_,
    select,
    update,
)
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import InstrumentedAttribute
from sqlalchemy.sql.base import ExecutableOption
from sqlalchemy.sql.dml import ReturningInsert
from sqlalchemy.sql.functions import now
from sqlalchemy.sql.selectable import TypedReturnsRows

from notora.utils.validation import validate_exclusive_presence
from notora.v1.enums.base import OrderByDirections
from notora.v1.models.base import BaseModel, GenericBaseModel
from notora.v1.schemas.base import Filter, OrderBy, OrFilterGroup

type Filters = Filter | OrFilterGroup


class HasWhere(Protocol):
    def where(self, *args: Any) -> 'HasWhere': ...


class BaseRepo[PKType, ModelType: GenericBaseModel]:
    load_options: Iterable[ExecutableOption] = []
    default_filters: Iterable[Filters] = []

    def __init__(self, model: type[ModelType], default_limit: int = 20):
        self.model = model
        self.default_limit = default_limit

    def select(self) -> Select[tuple[ModelType]]:
        return select(self.model).options(*self.load_options)

    def create_or_skip(
        self,
        data: dict[str, Any],
        index_elements: Iterable[InstrumentedAttribute[Any]],
        index_where: Iterable[Filters] | None = None,
    ) -> ReturningInsert[tuple[ModelType]]:
        where = None if not index_where else and_(*self._get_query_predicates(index_where))
        return (
            insert(self.model)
            .values(**data)
            .on_conflict_do_nothing(index_elements=index_elements, index_where=where)
            .returning(self.model)
            .options(*self.load_options)
        )

    def create(self, data: dict[str, Any]) -> ReturningInsert[tuple[ModelType]]:
        return insert(self.model).values(**data).returning(self.model).options(*self.load_options)

    def bulk_create(self, data: Sequence[dict[str, Any]]) -> ReturningInsert[tuple[ModelType]]:
        return insert(self.model).values(data).returning(self.model).options(*self.load_options)

    @overload
    def upsert(
        self,
        data: dict[str, Any],
        *,
        update_include_fields: Iterable[str] | None = None,
        index_elements: Iterable[InstrumentedAttribute[Any]] | None = None,
        index_where: Iterable[Filters] | None = None,
    ) -> ReturningInsert[tuple[ModelType]]: ...

    @overload
    def upsert(
        self,
        data: dict[str, Any],
        *,
        update_exclude_fields: Iterable[str] | None = None,
        index_elements: Iterable[InstrumentedAttribute[Any]] | None = None,
        index_where: Iterable[Filters] | None = None,
    ) -> ReturningInsert[tuple[ModelType]]: ...

    def upsert(
        self,
        data: dict[str, Any],
        *,
        update_include_fields: Iterable[str] | None = None,
        update_exclude_fields: Iterable[str] | None = None,
        index_elements: Iterable[InstrumentedAttribute[Any]] | None = None,
        index_where: Iterable[Filters] | None = None,
    ) -> ReturningInsert[tuple[ModelType]]:
        validate_exclusive_presence(update_include_fields, update_exclude_fields)
        if update_include_fields is not None:
            update_data = {
                key: value for key, value in data.items() if key in update_include_fields
            }
        elif update_exclude_fields is not None:
            update_data = {
                key: value for key, value in data.items() if key not in update_exclude_fields
            }

        where = None if not index_where else and_(*self._get_query_predicates(index_where))
        return (
            insert(self.model)
            .values(**data)
            .on_conflict_do_update(
                index_elements=index_elements or (self.model.id,),
                index_where=where,
                set_=update_data,
            )
            .returning(self.model)
            .options(*self.load_options)
        )

    def list_(
        self,
        base_query: Select[tuple[ModelType]] | None = None,
        filters: Iterable[Filters] = (),
        limit: int | None = None,
        offset: int = 0,
        order_by: Iterable[OrderBy] = (),
    ) -> Select[tuple[ModelType]]:
        query = base_query if base_query is not None else self.select()
        query = self.add_filters(query, filters)
        query = self.add_order_by(query, order_by)
        return query.limit(limit or self.default_limit).offset(offset)

    def retrieve(self, entity_id: PKType | ScalarSelect[PKType]) -> Select[tuple[ModelType]]:
        return self.list_(limit=1, filters=[Filter(field='id', op='=', value=entity_id)])

    def retrieve_by(
        self,
        filters: Iterable[Filters] = (),
        order_by: Iterable[OrderBy] = (),
    ) -> Select[tuple[ModelType]]:
        query = self.select()
        query = self.add_filters(query, filters)
        query = self.add_order_by(query, order_by)
        return query

    def update(
        self,
        entity_id: PKType | ScalarSelect[PKType],
        data: dict[str, object],
    ) -> TypedReturnsRows[tuple[ModelType]]:
        return self.update_by(
            data,
            filters=[Filter(field='id', op='eq', value=entity_id)],
        )

    def update_by(
        self,
        data: dict[str, object],
        filters: Iterable[Filters] = (),
    ) -> TypedReturnsRows[tuple[ModelType]]:
        query = update(self.model).values(**data)
        query = self.add_filters(query, filters)
        return query.returning(self.model).options(*self.load_options)

    def hard_delete(self, entity_id: PKType) -> TypedReturnsRows[tuple[ModelType]]:
        return self.hard_delete_by(
            filters=[Filter(field='id', op='eq', value=entity_id)],
        )

    def hard_delete_by(
        self, filters: Iterable[Filters] = ()
    ) -> TypedReturnsRows[tuple[ModelType]]:
        query = delete(self.model)
        query = self.add_filters(query, filters)
        return query.returning(self.model).options(*self.load_options)

    def number_of_records(self, filters: Iterable[Filters] = ()) -> Select[tuple[int]]:
        query = select(func.count()).select_from(self.model)
        query = self.add_filters(query, filters)
        return query

    def add_filters[T: HasWhere](self, query: T, filters: Iterable[Filters] = ()) -> T:
        filters = (*filters, *self.default_filters)
        for predicate in self._get_query_predicates(filters):
            query = cast(T, query.where(predicate))
        return query

    def add_order_by[T: Any](self, query: Select[T], order_by: Iterable[OrderBy]) -> Select[T]:
        orders: list[UnaryExpression[Any]] = []
        secondary_sort_model: type[ModelType] = self.model

        for order in order_by:
            target_model = order.model or self.model
            field = getattr(target_model, order.field)
            match order.direction:
                case OrderByDirections.ASC:
                    direction_func = asc
                case OrderByDirections.DESC:
                    direction_func = desc
            orders.append(direction_func(field))
            if order.model is not None:
                secondary_sort_model = order.model

        return query.order_by(*orders, secondary_sort_model.id)

    def _get_query_predicates(self, filters: Iterable[Filters]) -> Iterable[Any]:  # noqa: C901, PLR0912
        predicates = []
        for filter_ in filters:
            match filter_:
                case OrFilterGroup(filters=or_filters):
                    or_predicates = or_(*self._get_query_predicates(or_filters))
                    predicates.append(or_predicates)
                case Filter():
                    target_model = filter_.model or self.model
                    field = getattr(target_model, filter_.field)
                    match filter_:
                        case Filter(op='eq' | '=', value=None):
                            predicates.append(field.is_(None))
                        case Filter(op='is', value=v1):
                            predicates.append(field.is_(v1))
                        case Filter(value=None):
                            continue
                        case Filter(op='eq' | '=', value=v2):
                            predicates.append(field == v2)
                        case Filter(op='ilike' | '~=', value=v3):
                            predicates.append(field.ilike(f'%{v3}%'))
                        case Filter(op='in', value=[] | () | set(())):
                            predicates.append(false())
                        case Filter(op='in', value=v4):
                            predicates.append(field.in_(v4))
                        case Filter(op='gt' | '>', value=v5):
                            predicates.append(field > v5)
                        case Filter(op='ge' | '>=', value=v6):
                            predicates.append(field >= v6)
                        case Filter(op='lt' | '<', value=v7):
                            predicates.append(field < v7)
                        case Filter(op='le' | '<=', value=v8):
                            predicates.append(field <= v8)
        return predicates


class SoftDeletableRepo[
    PKType,
    ModelType: BaseModel,
](BaseRepo[PKType, ModelType]):
    default_filters = (Filter(field='deleted_at', op='is', value=null()),)

    @override
    def select(self) -> Select[tuple[ModelType]]:
        return self.add_filters(super().select())

    @override
    def create_or_skip(
        self,
        data: dict[str, Any],
        index_elements: Iterable[InstrumentedAttribute[Any]],
        index_where: Iterable[Filters] | None = None,
    ) -> ReturningInsert[tuple[ModelType]]:
        index_where = index_where or (Filter(field='deleted_at', op='is', value=null()),)
        return super().create_or_skip(
            data=data, index_elements=index_elements, index_where=index_where
        )

    @overload
    def upsert(
        self,
        data: dict[str, Any],
        *,
        update_include_fields: Iterable[str] | None = None,
        index_elements: Iterable[InstrumentedAttribute[Any]] | None = None,
        index_where: Iterable[Filters] | None = None,
    ) -> ReturningInsert[tuple[ModelType]]: ...

    @overload
    def upsert(
        self,
        data: dict[str, Any],
        *,
        update_exclude_fields: Iterable[str] | None = None,
        index_elements: Iterable[InstrumentedAttribute[Any]] | None = None,
        index_where: Iterable[Filters] | None = None,
    ) -> ReturningInsert[tuple[ModelType]]: ...

    @override
    def upsert(
        self,
        data: dict[str, Any],
        *,
        update_include_fields: Iterable[str] | None = None,
        update_exclude_fields: Iterable[str] | None = None,
        index_elements: Iterable[InstrumentedAttribute[Any]] | None = None,
        index_where: Iterable[Filters] | None = None,
    ) -> ReturningInsert[tuple[ModelType]]:
        index_where = index_where or (Filter(field='deleted_at', op='is', value=null()),)
        validate_exclusive_presence(update_include_fields, update_exclude_fields)
        if update_include_fields is not None:
            query = super().upsert(
                data=data,
                update_include_fields=update_include_fields,
                index_elements=index_elements,
                index_where=index_where,
            )
        elif update_exclude_fields is not None:
            query = super().upsert(
                data=data,
                update_exclude_fields=update_exclude_fields,
                index_elements=index_elements,
                index_where=index_where,
            )
        return query

    def soft_delete(
        self,
        entity_id: PKType,
    ) -> TypedReturnsRows[tuple[ModelType]]:
        return self.soft_delete_by([Filter(field='id', op='eq', value=entity_id)])

    def soft_delete_by(
        self,
        filters: Iterable[Filters] = (),
    ) -> TypedReturnsRows[tuple[ModelType]]:
        query = update(self.model).values({'deleted_at': now()})
        query = self.add_filters(query, filters)
        return query.returning(self.model)
