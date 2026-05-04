from datetime import UTC, datetime, timedelta, timezone
from ipaddress import IPv4Address, IPv6Address
from uuid import uuid4

import pytest

from notora.v1.schemas.base import (
    AdminMeta,
    ClientMeta,
    Filter,
    OrFilterGroup,
    OrderBy,
    PaginationMetaSchema,
    datetime_encoder,
    normalize_datetime_to_utc,
    utc_datetime_encoder,
)
from notora.v1.enums.base import OrderByDirections


class TestNormalizeDatetimeToUtc:
    def test_naive_datetime_gets_utc_tzinfo(self) -> None:
        naive = datetime(2024, 6, 15, 12, 0, 0)
        result = normalize_datetime_to_utc(naive)
        assert result.tzinfo == UTC

    def test_naive_datetime_value_unchanged(self) -> None:
        naive = datetime(2024, 6, 15, 12, 0, 0)
        result = normalize_datetime_to_utc(naive)
        assert result.replace(tzinfo=None) == naive

    def test_utc_aware_datetime_unchanged(self) -> None:
        aware = datetime(2024, 6, 15, 12, 0, 0, tzinfo=UTC)
        result = normalize_datetime_to_utc(aware)
        assert result == aware

    def test_offset_aware_datetime_converted_to_utc(self) -> None:
        tz_plus2 = timezone(timedelta(hours=2))
        aware = datetime(2024, 6, 15, 14, 0, 0, tzinfo=tz_plus2)
        result = normalize_datetime_to_utc(aware)
        assert result == datetime(2024, 6, 15, 12, 0, 0, tzinfo=UTC)
        assert result.tzinfo == UTC

    def test_negative_offset_converted_to_utc(self) -> None:
        tz_minus5 = timezone(timedelta(hours=-5))
        aware = datetime(2024, 6, 15, 7, 0, 0, tzinfo=tz_minus5)
        result = normalize_datetime_to_utc(aware)
        assert result == datetime(2024, 6, 15, 12, 0, 0, tzinfo=UTC)


class TestUtcDatetimeEncoder:
    def test_returns_iso_string_with_z(self) -> None:
        dt = datetime(2024, 1, 20, 9, 15, 30, tzinfo=UTC)
        result = utc_datetime_encoder(dt)
        assert result == '2024-01-20T09:15:30Z'

    def test_naive_datetime_treated_as_utc(self) -> None:
        naive = datetime(2024, 1, 20, 9, 15, 30)
        result = utc_datetime_encoder(naive)
        assert result == '2024-01-20T09:15:30Z'

    def test_offset_aware_datetime_converted(self) -> None:
        tz_plus3 = timezone(timedelta(hours=3))
        dt = datetime(2024, 1, 20, 12, 15, 30, tzinfo=tz_plus3)
        result = utc_datetime_encoder(dt)
        assert result == '2024-01-20T09:15:30Z'

    def test_does_not_contain_plus00_00(self) -> None:
        dt = datetime(2024, 6, 1, 0, 0, 0, tzinfo=UTC)
        result = utc_datetime_encoder(dt)
        assert '+00:00' not in result


class TestDatetimeEncoder:
    def test_returns_float_timestamp(self) -> None:
        dt = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
        result = datetime_encoder(dt)
        assert isinstance(result, float)

    def test_naive_datetime_treated_as_utc(self) -> None:
        naive = datetime(2024, 1, 1, 0, 0, 0)
        aware = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
        assert datetime_encoder(naive) == datetime_encoder(aware)

    def test_offset_datetime_normalized(self) -> None:
        tz_plus2 = timezone(timedelta(hours=2))
        offset = datetime(2024, 1, 1, 2, 0, 0, tzinfo=tz_plus2)
        utc = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
        assert datetime_encoder(offset) == datetime_encoder(utc)


class TestPaginationMetaSchema:
    def test_first_page_full(self) -> None:
        meta = PaginationMetaSchema.calculate(total=100, limit=10, offset=0)
        assert meta.current_page == 1
        assert meta.last_page == 10
        assert meta.total == 100
        assert meta.limit == 10

    def test_second_page(self) -> None:
        meta = PaginationMetaSchema.calculate(total=100, limit=10, offset=10)
        assert meta.current_page == 2

    def test_last_page_calculated(self) -> None:
        meta = PaginationMetaSchema.calculate(total=25, limit=10, offset=0)
        assert meta.last_page == 3

    def test_zero_total_gives_page_1(self) -> None:
        meta = PaginationMetaSchema.calculate(total=0, limit=10, offset=0)
        assert meta.current_page == 1
        assert meta.last_page == 1
        assert meta.total == 0

    def test_exact_multiple_total(self) -> None:
        meta = PaginationMetaSchema.calculate(total=20, limit=10, offset=0)
        assert meta.last_page == 2

    def test_total_less_than_limit_gives_page_1(self) -> None:
        meta = PaginationMetaSchema.calculate(total=5, limit=10, offset=0)
        assert meta.current_page == 1
        assert meta.last_page == 1


class TestAdminMeta:
    def test_deleted_at_is_none_by_default(self) -> None:
        meta = AdminMeta(
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
            updated_at=datetime(2024, 1, 1, tzinfo=UTC),
        )
        assert meta.deleted_at is None

    def test_deleted_at_can_be_set(self) -> None:
        dt = datetime(2024, 6, 1, 12, 0, tzinfo=UTC)
        meta = AdminMeta(
            created_at=datetime(2024, 1, 1, tzinfo=UTC),
            updated_at=datetime(2024, 1, 1, tzinfo=UTC),
            deleted_at=dt,
        )
        assert meta.deleted_at == dt

    def test_timestamps_normalized_to_utc(self) -> None:
        naive = datetime(2024, 1, 1, 10, 0, 0)
        meta = AdminMeta(created_at=naive, updated_at=naive)
        assert meta.created_at.tzinfo == UTC
        assert meta.updated_at.tzinfo == UTC


class TestClientMeta:
    def test_both_fields_none_by_default(self) -> None:
        client = ClientMeta()
        assert client.ip_address is None
        assert client.user_agent is None

    def test_ipv4_address_accepted(self) -> None:
        client = ClientMeta(ip_address=IPv4Address('127.0.0.1'))
        assert isinstance(client.ip_address, IPv4Address)

    def test_ipv6_address_accepted(self) -> None:
        client = ClientMeta(ip_address=IPv6Address('::1'))
        assert isinstance(client.ip_address, IPv6Address)

    def test_user_agent_stored(self) -> None:
        client = ClientMeta(user_agent='Mozilla/5.0')
        assert client.user_agent == 'Mozilla/5.0'

    def test_ip_address_serialized_as_string(self) -> None:
        client = ClientMeta(ip_address=IPv4Address('192.168.0.1'))
        dumped = client.model_dump()
        assert dumped['ip_address'] == '192.168.0.1'


class TestFilter:
    def test_default_op_is_eq(self) -> None:
        f = Filter(field='name', value='alice')
        assert f.op == '='

    def test_custom_op(self) -> None:
        f = Filter(field='age', op='gt', value=18)
        assert f.op == 'gt'

    def test_value_none_allowed(self) -> None:
        f = Filter(field='deleted_at', op='is', value=None)
        assert f.value is None

    def test_model_none_by_default(self) -> None:
        f = Filter(field='name', value='x')
        assert f.model is None

    def test_model_can_be_set(self) -> None:
        class FakeModel:
            pass
        f = Filter(field='name', value='x', model=FakeModel)
        assert f.model is FakeModel

    def test_all_ops_accepted(self) -> None:
        valid_ops = ('eq', '=', 'ilike', '~=', 'is', 'is_not', 'in', 'gt', '>', 'ge', '>=', 'lt', '<', 'le', '<=')
        for op in valid_ops:
            f = Filter(field='x', op=op, value=1)  # type: ignore[arg-type]
            assert f.op == op


class TestOrFilterGroup:
    def test_stores_filters(self) -> None:
        f1 = Filter(field='name', value='a')
        f2 = Filter(field='name', value='b')
        group = OrFilterGroup(filters=[f1, f2])
        assert len(group.filters) == 2

    def test_empty_filters_allowed(self) -> None:
        group = OrFilterGroup(filters=[])
        assert group.filters == []


class TestOrderBy:
    def test_default_direction_is_asc(self) -> None:
        ob = OrderBy(field='name')
        assert ob.direction == OrderByDirections.ASC

    def test_desc_direction(self) -> None:
        ob = OrderBy(field='name', direction=OrderByDirections.DESC)
        assert ob.direction == OrderByDirections.DESC

    def test_model_none_by_default(self) -> None:
        ob = OrderBy(field='name')
        assert ob.model is None

    def test_model_can_be_set(self) -> None:
        class FakeModel:
            pass
        ob = OrderBy(field='name', model=FakeModel)
        assert ob.model is FakeModel
