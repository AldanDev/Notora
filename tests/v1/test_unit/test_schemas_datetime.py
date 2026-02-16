from datetime import UTC, datetime, timedelta, timezone
from uuid import uuid4

from notora.v1.schemas.base import BaseTokenSchema, CreateUpdateMeta


def test_create_update_meta_normalizes_naive_datetimes_to_utc() -> None:
    naive_dt = datetime(2026, 1, 20, 9, 15, 30, tzinfo=UTC).replace(tzinfo=None)
    schema = CreateUpdateMeta(
        created_at=naive_dt,
        updated_at=naive_dt,
    )

    assert schema.created_at == datetime(2026, 1, 20, 9, 15, 30, tzinfo=UTC)
    assert schema.updated_at == datetime(2026, 1, 20, 9, 15, 30, tzinfo=UTC)
    assert schema.model_dump(mode='json') == {
        'created_at': '2026-01-20T09:15:30Z',
        'updated_at': '2026-01-20T09:15:30Z',
    }


def test_create_update_meta_converts_offset_datetime_to_utc() -> None:
    utc_plus_3 = timezone(timedelta(hours=3))
    schema = CreateUpdateMeta(
        created_at=datetime(2026, 1, 20, 12, 15, 30, tzinfo=utc_plus_3),
        updated_at=datetime(2026, 1, 20, 12, 15, 30, tzinfo=utc_plus_3),
    )

    assert schema.created_at == datetime(2026, 1, 20, 9, 15, 30, tzinfo=UTC)
    assert schema.updated_at == datetime(2026, 1, 20, 9, 15, 30, tzinfo=UTC)
    assert schema.model_dump(mode='json') == {
        'created_at': '2026-01-20T09:15:30Z',
        'updated_at': '2026-01-20T09:15:30Z',
    }


def test_base_token_timestamp_treats_naive_datetime_as_utc() -> None:
    naive_dt = datetime(2026, 1, 20, 9, 15, 30, tzinfo=UTC).replace(tzinfo=None)
    token = BaseTokenSchema(
        sub=uuid4(),
        iss='issuer',
        nbf=naive_dt,
        exp=naive_dt,
        iat=naive_dt,
    )

    utc_dt = datetime(2026, 1, 20, 9, 15, 30, tzinfo=UTC)
    assert token.nbf == utc_dt
    assert token.model_dump()['nbf'] == utc_dt.timestamp()
    assert token.model_dump(mode='json')['exp'] == '2026-01-20T09:15:30Z'
