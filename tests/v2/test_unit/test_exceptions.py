from uuid import uuid4

import pytest

from notora.v2.exceptions.common import AlreadyExistsError, FKNotFoundError, NotFoundError

_ENTITY_ID_INT = 42

def test_fk_not_found_error_stores_fk_name() -> None:
    err = FKNotFoundError('msg', fk_name='profile_user_id_fkey', table_name='profile')
    assert err.fk_name == 'profile_user_id_fkey'

def test_fk_not_found_error_stores_table_name() -> None:
    err = FKNotFoundError('msg', fk_name='fk', table_name='orders')
    assert err.table_name == 'orders'

def test_fk_not_found_error_message_is_accessible() -> None:
    err = FKNotFoundError('Related object not found.', fk_name='fk', table_name='tbl')
    assert str(err) == 'Related object not found.'

def test_fk_not_found_error_is_exception() -> None:
    err = FKNotFoundError('msg', fk_name='fk', table_name='tbl')
    assert isinstance(err, Exception)

def test_fk_not_found_error_can_be_raised_and_caught() -> None:
    msg = 'err'
    with pytest.raises(FKNotFoundError) as exc_info:
        raise FKNotFoundError(msg, fk_name='fk', table_name='tbl')
    assert exc_info.value.fk_name == 'fk'
    assert exc_info.value.table_name == 'tbl'

def test_already_exists_error_default_message() -> None:
    err = AlreadyExistsError()
    assert str(err) == 'Entity already exists.'

def test_already_exists_error_custom_message() -> None:
    err = AlreadyExistsError('Custom message.')
    assert str(err) == 'Custom message.'

def test_already_exists_error_constraint_name_stored() -> None:
    err = AlreadyExistsError(constraint_name='users_email_key')
    assert err.constraint_name == 'users_email_key'

def test_already_exists_error_constraint_name_none_by_default() -> None:
    err = AlreadyExistsError()
    assert err.constraint_name is None

def test_already_exists_error_message_and_constraint_together() -> None:
    err = AlreadyExistsError('Dup', constraint_name='my_constraint')
    assert str(err) == 'Dup'
    assert err.constraint_name == 'my_constraint'

def test_already_exists_error_is_exception() -> None:
    assert isinstance(AlreadyExistsError(), Exception)

def test_already_exists_error_can_be_raised_and_caught() -> None:
    msg = 'dup'
    with pytest.raises(AlreadyExistsError):
        raise AlreadyExistsError(msg)

def test_not_found_error_entity_id_none_by_default() -> None:
    err: NotFoundError[None] = NotFoundError('not found')
    assert err.entity_id is None

def test_not_found_error_entity_id_stored() -> None:
    err = NotFoundError('not found', entity_id=_ENTITY_ID_INT)
    assert err.entity_id == _ENTITY_ID_INT

def test_not_found_error_entity_id_uuid() -> None:
    uid = uuid4()
    err = NotFoundError('not found', entity_id=uid)
    assert err.entity_id == uid

def test_not_found_error_message_preserved() -> None:
    err: NotFoundError[None] = NotFoundError('Resource not found.')
    assert str(err) == 'Resource not found.'

def test_not_found_error_is_exception() -> None:
    assert isinstance(NotFoundError('x'), Exception)

def test_not_found_error_can_be_raised_and_caught() -> None:
    msg = 'missing'
    with pytest.raises(NotFoundError):
        raise NotFoundError(msg)

def test_not_found_error_no_positional_args() -> None:
    err: NotFoundError[None] = NotFoundError()
    assert err.entity_id is None
