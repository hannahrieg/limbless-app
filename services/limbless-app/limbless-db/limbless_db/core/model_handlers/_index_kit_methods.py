import math
from typing import Optional

import sqlalchemy as sa

from ...categories import IndexTypeEnum, LabProtocolEnum
from ... import models, PAGE_LIMIT
from .. import exceptions


def create_index_kit(
    self, identifier: str, name: str,
    supported_protocols: list[LabProtocolEnum],
    type: IndexTypeEnum,
) -> models.IndexKit:
    if not (persist_session := self._session is not None):
        self.open_session()

    if self._session.query(models.IndexKit).where(models.IndexKit.name == name).first():
        raise exceptions.NotUniqueValue(f"index_kit with name '{name}', already exists.")

    seq_kit = models.IndexKit(
        identifier=identifier.strip(),
        name=name.strip(),
        type_id=type.id,
        supported_protocol_ids=[p.id for p in supported_protocols]
    )
    self._session.add(seq_kit)
    self._session.commit()
    self._session.refresh(seq_kit)

    if not persist_session:
        self.close_session()
    return seq_kit


def get_index_kit(self, id: int) -> Optional[models.IndexKit]:
    if not (persist_session := self._session is not None):
        self.open_session()

    res = self._session.get(models.IndexKit, id)

    if not persist_session:
        self.close_session()

    return res


def get_index_kit_by_name(self, name: str) -> Optional[models.IndexKit]:
    if not (persist_session := self._session is not None):
        self.open_session()

    res = self._session.query(models.IndexKit).where(models.IndexKit.name == name).first()

    if not persist_session:
        self.close_session()
    return res


def get_index_kits(
    self, type_in: Optional[list[IndexTypeEnum]] = None,
    limit: Optional[int] = PAGE_LIMIT, offset: Optional[int] = 0,
    sort_by: Optional[str] = None, descending: bool = False,
) -> tuple[list[models.IndexKit], int]:
    if not (persist_session := self._session is not None):
        self.open_session()

    query = self._session.query(models.IndexKit)

    if type_in is not None:
        query = query.where(models.IndexKit.type_id.in_([t.id for t in type_in]))

    n_pages = math.ceil(query.count() / limit) if limit is not None else 1

    if sort_by is not None:
        attr = getattr(models.IndexKit, sort_by)
        if descending:
            attr = attr.desc()
        query = query.order_by(attr)

    if limit is not None:
        query = query.limit(limit)

    if offset is not None:
        query = query.offset(offset)

    res = query.all()

    if not persist_session:
        self.close_session()

    return res, n_pages


def query_index_kits(
    self, word: str, limit: Optional[int] = PAGE_LIMIT,
    type_in: Optional[list[IndexTypeEnum]] = None,
) -> list[models.IndexKit]:
    if not (persist_session := self._session is not None):
        self.open_session()

    query = sa.select(models.IndexKit)

    if type_in is not None:
        query = query.where(models.IndexKit.type_id.in_([t.id for t in type_in]))

    query = query.order_by(
        sa.func.similarity(models.IndexKit.identifier + ' ' + models.IndexKit.name, word).desc()
    )

    if limit is not None:
        query = query.limit(limit)

    res = self._session.scalars(query).all()

    if not persist_session:
        self.close_session()
    return res
