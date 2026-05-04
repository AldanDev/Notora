"""Tests for v2 schemas.base — ClientMeta, PaginationMetaSchema."""

from ipaddress import IPv4Address, IPv6Address

from notora.v2.schemas.base import ClientMeta, PaginationMetaSchema

_TOTAL_100 = 100
_LIMIT = 10

def test_client_meta_both_fields_none_by_default() -> None:
    client = ClientMeta()
    assert client.ip_address is None
    assert client.user_agent is None

def test_client_meta_ipv4_address_accepted() -> None:
    client = ClientMeta(ip_address=IPv4Address('192.168.1.1'))
    assert isinstance(client.ip_address, IPv4Address)

def test_client_meta_ipv6_address_accepted() -> None:
    client = ClientMeta(ip_address=IPv6Address('::1'))
    assert isinstance(client.ip_address, IPv6Address)

def test_client_meta_user_agent_stored() -> None:
    client = ClientMeta(user_agent='Mozilla/5.0')
    assert client.user_agent == 'Mozilla/5.0'

def test_client_meta_ip_serialized_as_string_in_dict() -> None:
    client = ClientMeta(ip_address=IPv4Address('10.0.0.1'))
    dumped = client.model_dump()
    assert dumped['ip_address'] == '10.0.0.1'

def test_pagination_meta_negative_total_clamped_to_zero() -> None:
    meta = PaginationMetaSchema.calculate(total=-5, limit=_LIMIT, offset=0)
    assert meta.total == 0

def test_pagination_meta_zero_total_preserved() -> None:
    meta = PaginationMetaSchema.calculate(total=0, limit=_LIMIT, offset=0)
    assert meta.total == 0

def test_pagination_meta_positive_total_preserved() -> None:
    meta = PaginationMetaSchema.calculate(total=_TOTAL_100, limit=_LIMIT, offset=0)
    assert meta.total == _TOTAL_100
