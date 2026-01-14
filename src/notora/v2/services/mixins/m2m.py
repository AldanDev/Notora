from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any, Literal

from sqlalchemy import delete, insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from notora.v2.models.base import GenericBaseModel
from notora.v2.services.mixins.accessors import RepositoryAccessorMixin

type M2MSyncMode = Literal['replace', 'add', 'remove']


@dataclass(slots=True)
class ManyToManyRelation[ModelType: GenericBaseModel]:
    payload_field: str
    association_model: type[ModelType]
    left_key: InstrumentedAttribute[Any]
    right_key: InstrumentedAttribute[Any]
    row_factory: Callable[[Any, Any], dict[str, Any]] | None = None

    def build_row(self, owner_id: Any, target_id: Any) -> dict[str, Any]:
        if self.row_factory:
            return self.row_factory(owner_id, target_id)
        return {self.left_key.key: owner_id, self.right_key.key: target_id}


class ManyToManySyncMixin[PKType, ModelType: GenericBaseModel](
    RepositoryAccessorMixin[PKType, ModelType],
):
    many_to_many_relations: Sequence[ManyToManyRelation[Any]] = ()
    m2m_sync_mode: M2MSyncMode = 'replace'

    def split_m2m_payload(
        self,
        payload: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Sequence[Any]]]:
        if not self.many_to_many_relations:
            return payload, {}
        data = dict(payload)
        relation_payload: dict[str, Sequence[Any]] = {}
        for relation in self.many_to_many_relations:
            if relation.payload_field in data:
                relation_payload[relation.payload_field] = data.pop(relation.payload_field) or ()
        return data, relation_payload

    async def sync_m2m_relations(  # noqa: C901
        self,
        session: AsyncSession,
        owner_id: PKType,
        relation_payload: dict[str, Sequence[Any]],
        *,
        mode: M2MSyncMode | None = None,
    ) -> None:
        sync_mode = mode or self.m2m_sync_mode
        if sync_mode not in {'replace', 'add', 'remove'}:
            msg = 'm2m sync mode must be replace, add, or remove.'
            raise ValueError(msg)
        for relation in self.many_to_many_relations:
            if relation.payload_field not in relation_payload:
                continue
            target_ids = list(dict.fromkeys(relation_payload[relation.payload_field] or ()))
            if sync_mode == 'replace':
                delete_stmt = delete(relation.association_model).where(
                    relation.left_key == owner_id
                )
                await session.execute(delete_stmt)
            elif not target_ids:
                continue
            if not target_ids:
                continue
            if sync_mode == 'remove':
                delete_stmt = delete(relation.association_model).where(
                    relation.left_key == owner_id,
                    relation.right_key.in_(target_ids),
                )
                await session.execute(delete_stmt)
                continue
            if sync_mode == 'add':
                existing = (
                    await session.scalars(
                        select(relation.right_key).where(
                            relation.left_key == owner_id,
                            relation.right_key.in_(target_ids),
                        )
                    )
                ).all()
                existing_set = set(existing)
                target_ids = [
                    target_id for target_id in target_ids if target_id not in existing_set
                ]
                if not target_ids:
                    continue
            rows = [relation.build_row(owner_id, target_id) for target_id in target_ids]
            await session.execute(insert(relation.association_model).values(rows))
