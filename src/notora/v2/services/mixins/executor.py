import re
from typing import Any, ClassVar, cast

from sqlalchemy import exc
from sqlalchemy.engine import Result, ScalarResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Executable
from sqlalchemy.sql.selectable import TypedReturnsRows

from notora.v2.exceptions.common import AlreadyExistsError, FKNotFoundError, NotFoundError
from notora.v2.models.base import GenericBaseModel


class SessionExecutorMixin[PKType, ModelType: GenericBaseModel]:
    _unique_violation_errors: ClassVar[dict[str, str]] = {}
    _fk_violation_errors: ClassVar[dict[str, str]] = {}

    _unique_constraint_pattern = re.compile(
        r'.*duplicate key value violates unique constraint "(?P<name>\w+)"',
    )
    _fk_constraint_pattern = re.compile(
        r'.*insert or update on table "(?P<table_name>\w+)" '
        r'violates foreign key constraint "(?P<fk_name>\w+)"',
    )

    @property
    def _not_found_error(self) -> str:
        return f'{self.__class__.__name__.removesuffix("Service")} not found.'

    async def execute(
        self,
        session: AsyncSession,
        statement: Executable,
    ) -> Result[Any]:
        try:
            return await session.execute(statement)
        except exc.IntegrityError as err:
            raise self._translate_integrity_error(err) from err

    async def execute_scalars(
        self,
        session: AsyncSession,
        statement: Executable,
    ) -> ScalarResult[Any]:
        result = await self.execute(session, statement)
        return result.scalars()

    async def execute_scalars_all(
        self,
        session: AsyncSession,
        statement: Executable,
    ) -> list[Any]:
        return list((await self.execute_scalars(session, statement)).all())

    async def execute_scalar_one(
        self,
        session: AsyncSession,
        statement: Executable,
    ) -> Any:
        result = await self.execute(session, statement)
        return result.scalar_one()

    async def execute_for_one(
        self,
        session: AsyncSession,
        statement: TypedReturnsRows[tuple[ModelType]],
    ) -> ModelType:
        result = await self.execute(session, statement)
        entity = result.unique().scalar_one_or_none()
        if entity is None:
            raise NotFoundError[PKType](self._not_found_error)
        return cast(ModelType, entity)

    async def execute_optional(
        self,
        session: AsyncSession,
        statement: TypedReturnsRows[tuple[ModelType]],
    ) -> ModelType | None:
        result = await self.execute(session, statement)
        return cast(ModelType | None, result.unique().scalar_one_or_none())

    def _translate_integrity_error(self, err: exc.IntegrityError) -> Exception:
        if match := self._fk_constraint_pattern.match(err.args[0]):
            fk_name = match.group('fk_name')
            table_name = match.group('table_name')
            return FKNotFoundError(
                self._fk_violation_errors.get(fk_name, 'Related object not found.'),
                fk_name=fk_name,
                table_name=table_name,
            )
        if match := self._unique_constraint_pattern.match(err.args[0]):
            constraint = match.group('name')
            return AlreadyExistsError(
                self._unique_violation_errors.get(constraint, 'Entity already exists.'),
                constraint_name=constraint,
            )
        return err
