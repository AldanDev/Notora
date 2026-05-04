import pytest

from notora.v1.enums.base import OrderByDirections
from notora.v1.exceptions.common import AlreadyExistsError, FKNotFoundError, NotFoundError


class TestOrderByDirections:
    def test_asc_value(self) -> None:
        assert OrderByDirections.ASC == 'asc'

    def test_desc_value(self) -> None:
        assert OrderByDirections.DESC == 'desc'

    def test_is_str_enum(self) -> None:
        assert isinstance(OrderByDirections.ASC, str)
        assert isinstance(OrderByDirections.DESC, str)

    def test_can_be_used_as_string(self) -> None:
        assert f'{OrderByDirections.ASC}' == 'asc'
        assert f'{OrderByDirections.DESC}' == 'desc'


class TestFKNotFoundError:
    def test_stores_fk_name(self) -> None:
        err = FKNotFoundError('msg', fk_name='user_id_fkey', table_name='post')
        assert err.fk_name == 'user_id_fkey'

    def test_stores_table_name(self) -> None:
        err = FKNotFoundError('msg', fk_name='user_id_fkey', table_name='post')
        assert err.table_name == 'post'

    def test_message_is_accessible(self) -> None:
        err = FKNotFoundError('Related object not found.', fk_name='fk', table_name='tbl')
        assert str(err) == 'Related object not found.'

    def test_is_exception(self) -> None:
        err = FKNotFoundError('msg', fk_name='fk', table_name='tbl')
        assert isinstance(err, Exception)

    def test_can_be_raised_and_caught(self) -> None:
        with pytest.raises(FKNotFoundError) as exc_info:
            raise FKNotFoundError('err', fk_name='fk', table_name='tbl')
        assert exc_info.value.fk_name == 'fk'


class TestAlreadyExistsError:
    def test_default_message(self) -> None:
        err = AlreadyExistsError()
        assert str(err) == 'Entity already exists.'

    def test_custom_message(self) -> None:
        err = AlreadyExistsError('Custom message.')
        assert str(err) == 'Custom message.'

    def test_constraint_name_stored(self) -> None:
        err = AlreadyExistsError(constraint_name='users_email_key')
        assert err.constraint_name == 'users_email_key'

    def test_constraint_name_none_by_default(self) -> None:
        err = AlreadyExistsError()
        assert err.constraint_name is None

    def test_message_and_constraint_together(self) -> None:
        err = AlreadyExistsError('Dup', constraint_name='my_constraint')
        assert str(err) == 'Dup'
        assert err.constraint_name == 'my_constraint'

    def test_is_exception(self) -> None:
        assert isinstance(AlreadyExistsError(), Exception)

    def test_can_be_raised_and_caught(self) -> None:
        with pytest.raises(AlreadyExistsError):
            raise AlreadyExistsError('dup')


class TestNotFoundError:
    def test_entity_id_none_by_default(self) -> None:
        err = NotFoundError('not found')
        assert err.entity_id is None

    def test_entity_id_stored(self) -> None:
        err = NotFoundError('not found', entity_id=42)
        assert err.entity_id == 42

    def test_entity_id_uuid(self) -> None:
        from uuid import uuid4
        uid = uuid4()
        err = NotFoundError('not found', entity_id=uid)
        assert err.entity_id == uid

    def test_message_preserved(self) -> None:
        err = NotFoundError('Resource not found.')
        assert str(err) == 'Resource not found.'

    def test_is_exception(self) -> None:
        assert isinstance(NotFoundError('x'), Exception)

    def test_can_be_raised_and_caught(self) -> None:
        with pytest.raises(NotFoundError):
            raise NotFoundError('missing')

    def test_no_positional_args(self) -> None:
        err = NotFoundError()
        assert err.entity_id is None
