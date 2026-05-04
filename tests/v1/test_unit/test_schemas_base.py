from datetime import UTC, datetime, timedelta, timezone
from ipaddress import IPv4Address, IPv6Address

from notora.v1.enums.base import OrderByDirections
from notora.v1.schemas.base import (
    AdminMeta,
    ClientMeta,
    Filter,
    OrderBy,
    OrFilterGroup,
    PaginationMetaSchema,
    datetime_encoder,
    normalize_datetime_to_utc,
    utc_datetime_encoder,
)

_LIMIT = 10
_TOTAL_100 = 100
_TOTAL_25 = 25
_TOTAL_20 = 20
_TOTAL_5 = 5
_LAST_PAGE_10 = 10
_LAST_PAGE_3 = 3
_LAST_PAGE_2 = 2
_SECOND_PAGE = 2
_FILTER_COUNT = 2


# ---------------------------------------------------------------------------
# normalize_datetime_to_utc
# ---------------------------------------------------------------------------

def test_normalize_datetime_naive_gets_utc_tzinfo() -> None:
    naive = datetime(2024, 6, 15, 12, 0, 0, tzinfo=UTC).replace(tzinfo=None)
    result = normalize_datetime_to_utc(naive)
    assert result.tzinfo == UTC


def test_normalize_datetime_naive_value_unchanged() -> None:
    naive = datetime(2024, 6, 15, 12, 0, 0, tzinfo=UTC).replace(tzinfo=None)
    result = normalize_datetime_to_utc(naive)
    assert result.replace(tzinfo=None) == naive


def test_normalize_datetime_utc_aware_unchanged() -> None:
    aware = datetime(2024, 6, 15, 12, 0, 0, tzinfo=UTC)
    result = normalize_datetime_to_utc(aware)
    assert result == aware


def test_normalize_datetime_offset_aware_converted_to_utc() -> None:
    tz_plus2 = timezone(timedelta(hours=2))
    aware = datetime(2024, 6, 15, 14, 0, 0, tzinfo=tz_plus2)
    result = normalize_datetime_to_utc(aware)
    assert result == datetime(2024, 6, 15, 12, 0, 0, tzinfo=UTC)
    assert result.tzinfo == UTC


def test_normalize_datetime_negative_offset_converted_to_utc() -> None:
    tz_minus5 = timezone(timedelta(hours=-5))
    aware = datetime(2024, 6, 15, 7, 0, 0, tzinfo=tz_minus5)
    result = normalize_datetime_to_utc(aware)
    assert result == datetime(2024, 6, 15, 12, 0, 0, tzinfo=UTC)


# ---------------------------------------------------------------------------
# utc_datetime_encoder
# ---------------------------------------------------------------------------

def test_utc_datetime_encoder_returns_iso_string_with_z() -> None:
    dt = datetime(2024, 1, 20, 9, 15, 30, tzinfo=UTC)
    result = utc_datetime_encoder(dt)
    assert result == '2024-01-20T09:15:30Z'


def test_utc_datetime_encoder_naive_datetime_treated_as_utc() -> None:
    naive = datetime(2024, 1, 20, 9, 15, 30, tzinfo=UTC).replace(tzinfo=None)
    result = utc_datetime_encoder(naive)
    assert result == '2024-01-20T09:15:30Z'


def test_utc_datetime_encoder_offset_aware_converted() -> None:
    tz_plus3 = timezone(timedelta(hours=3))
    dt = datetime(2024, 1, 20, 12, 15, 30, tzinfo=tz_plus3)
    result = utc_datetime_encoder(dt)
    assert result == '2024-01-20T09:15:30Z'


def test_utc_datetime_encoder_does_not_contain_plus00_00() -> None:
    dt = datetime(2024, 6, 1, 0, 0, 0, tzinfo=UTC)
    result = utc_datetime_encoder(dt)
    assert '+00:00' not in result


# ---------------------------------------------------------------------------
# datetime_encoder
# ---------------------------------------------------------------------------

def test_datetime_encoder_returns_float_timestamp() -> None:
    dt = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
    result = datetime_encoder(dt)
    assert isinstance(result, float)


def test_datetime_encoder_naive_datetime_treated_as_utc() -> None:
    naive = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC).replace(tzinfo=None)
    aware = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
    assert datetime_encoder(naive) == datetime_encoder(aware)


def test_datetime_encoder_offset_datetime_normalized() -> None:
    tz_plus2 = timezone(timedelta(hours=2))
    offset = datetime(2024, 1, 1, 2, 0, 0, tzinfo=tz_plus2)
    utc = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
    assert datetime_encoder(offset) == datetime_encoder(utc)


# ---------------------------------------------------------------------------
# PaginationMetaSchema
# ---------------------------------------------------------------------------

def test_pagination_meta_first_page_full() -> None:
    meta = PaginationMetaSchema.calculate(total=_TOTAL_100, limit=_LIMIT, offset=0)
    assert meta.current_page == 1
    assert meta.last_page == _LAST_PAGE_10
    assert meta.total == _TOTAL_100
    assert meta.limit == _LIMIT


def test_pagination_meta_second_page() -> None:
    meta = PaginationMetaSchema.calculate(total=_TOTAL_100, limit=_LIMIT, offset=_LIMIT)
    assert meta.current_page == _SECOND_PAGE


def test_pagination_meta_last_page_calculated() -> None:
    meta = PaginationMetaSchema.calculate(total=_TOTAL_25, limit=_LIMIT, offset=0)
    assert meta.last_page == _LAST_PAGE_3


def test_pagination_meta_zero_total_gives_page_1() -> None:
    meta = PaginationMetaSchema.calculate(total=0, limit=_LIMIT, offset=0)
    assert meta.current_page == 1
    assert meta.last_page == 1
    assert meta.total == 0


def test_pagination_meta_exact_multiple_total() -> None:
    meta = PaginationMetaSchema.calculate(total=_TOTAL_20, limit=_LIMIT, offset=0)
    assert meta.last_page == _LAST_PAGE_2


def test_pagination_meta_total_less_than_limit_gives_page_1() -> None:
    meta = PaginationMetaSchema.calculate(total=_TOTAL_5, limit=_LIMIT, offset=0)
    assert meta.current_page == 1
    assert meta.last_page == 1


# ---------------------------------------------------------------------------
# AdminMeta
# ---------------------------------------------------------------------------

def test_admin_meta_deleted_at_is_none_by_default() -> None:
    meta = AdminMeta(
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
        updated_at=datetime(2024, 1, 1, tzinfo=UTC),
    )
    assert meta.deleted_at is None


def test_admin_meta_deleted_at_can_be_set() -> None:
    dt = datetime(2024, 6, 1, 12, 0, tzinfo=UTC)
    meta = AdminMeta(
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
        updated_at=datetime(2024, 1, 1, tzinfo=UTC),
        deleted_at=dt,
    )
    assert meta.deleted_at == dt


def test_admin_meta_timestamps_normalized_to_utc() -> None:
    naive = datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC).replace(tzinfo=None)
    meta = AdminMeta(created_at=naive, updated_at=naive)
    assert meta.created_at.tzinfo == UTC
    assert meta.updated_at.tzinfo == UTC


# ---------------------------------------------------------------------------
# ClientMeta
# ---------------------------------------------------------------------------

def test_client_meta_both_fields_none_by_default() -> None:
    client = ClientMeta()
    assert client.ip_address is None
    assert client.user_agent is None


def test_client_meta_ipv4_address_accepted() -> None:
    client = ClientMeta(ip_address=IPv4Address('127.0.0.1'))
    assert isinstance(client.ip_address, IPv4Address)


def test_client_meta_ipv6_address_accepted() -> None:
    client = ClientMeta(ip_address=IPv6Address('::1'))
    assert isinstance(client.ip_address, IPv6Address)


def test_client_meta_user_agent_stored() -> None:
    client = ClientMeta(user_agent='Mozilla/5.0')
    assert client.user_agent == 'Mozilla/5.0'


def test_client_meta_ip_address_serialized_as_string() -> None:
    client = ClientMeta(ip_address=IPv4Address('192.168.0.1'))
    dumped = client.model_dump()
    assert dumped['ip_address'] == '192.168.0.1'


# ---------------------------------------------------------------------------
# Filter
# ---------------------------------------------------------------------------

def test_filter_default_op_is_eq() -> None:
    f = Filter(field='name', value='alice')
    assert f.op == '='


def test_filter_custom_op() -> None:
    f = Filter(field='age', op='gt', value=18)
    assert f.op == 'gt'


def test_filter_value_none_allowed() -> None:
    f = Filter(field='deleted_at', op='is', value=None)
    assert f.value is None


def test_filter_model_none_by_default() -> None:
    f = Filter(field='name', value='x')
    assert f.model is None


def test_filter_model_can_be_set() -> None:
    class FakeModel:
        pass
    f = Filter(field='name', value='x', model=FakeModel)
    assert f.model is FakeModel


def test_filter_all_ops_accepted() -> None:
    valid_ops = ('eq', '=', 'ilike', '~=', 'is', 'is_not', 'in', 'gt', '>', 'ge', '>=', 'lt', '<', 'le', '<=')
    for op in valid_ops:
        f = Filter(field='x', op=op, value=1)
        assert f.op == op


# ---------------------------------------------------------------------------
# OrFilterGroup
# ---------------------------------------------------------------------------

def test_or_filter_group_stores_filters() -> None:
    f1 = Filter(field='name', value='a')
    f2 = Filter(field='name', value='b')
    group = OrFilterGroup(filters=[f1, f2])
    assert len(group.filters) == _FILTER_COUNT


def test_or_filter_group_empty_filters_allowed() -> None:
    group = OrFilterGroup(filters=[])
    assert group.filters == []


# ---------------------------------------------------------------------------
# OrderBy
# ---------------------------------------------------------------------------

def test_order_by_default_direction_is_asc() -> None:
    ob = OrderBy(field='name')
    assert ob.direction == OrderByDirections.ASC


def test_order_by_desc_direction() -> None:
    ob = OrderBy(field='name', direction=OrderByDirections.DESC)
    assert ob.direction == OrderByDirections.DESC


def test_order_by_model_none_by_default() -> None:
    ob = OrderBy(field='name')
    assert ob.model is None


def test_order_by_model_can_be_set() -> None:
    class FakeModel:
        pass
    ob = OrderBy(field='name', model=FakeModel)
    assert ob.model is FakeModel
