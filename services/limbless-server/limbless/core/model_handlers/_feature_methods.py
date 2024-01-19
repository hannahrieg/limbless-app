import math
from typing import Optional

from sqlmodel import func, text, or_, and_

from ... import models, PAGE_LIMIT
from ...categories import FeatureType
from .. import exceptions


def create_feature(
    self,
    name: str,
    sequence: str,
    pattern: str,
    read: str,
    type: FeatureType,
    feature_kit_id: Optional[int] = None,
    target_name: Optional[str] = None,
    target_id: Optional[str] = None,
    commit: bool = True
) -> models.Feature:
    persist_session = self._session is not None
    if not self._session:
        self.open_session()

    if feature_kit_id is not None:
        if (_ := self._session.get(models.FeatureKit, feature_kit_id)) is None:
            raise exceptions.ElementDoesNotExist(f"Feature kit with id {feature_kit_id} does not exist")
        
        if self._session.query(models.Feature).where(
            models.Feature.name == name,
            models.Feature.feature_kit_id == feature_kit_id
        ).first():
            raise exceptions.NotUniqueValue(f"Feature with name '{name}' already exists in feature kit with id {feature_kit_id}")

    feature = models.Feature(
        name=name,
        sequence=sequence,
        pattern=pattern,
        read=read,
        type_id=type.value.id,
        target_name=target_name,
        target_id=target_id,
        feature_kit_id=feature_kit_id
    )
    self._session.add(feature)

    if commit:
        self._session.commit()
        self._session.refresh(feature)

    if not persist_session:
        self.close_session()
    return feature


def get_feature(self, feature_id: int) -> models.Feature:
    persist_session = self._session is not None
    if not self._session:
        self.open_session()

    res = self._session.get(models.Feature, feature_id)

    if not persist_session:
        self.close_session()
    return res


def get_features(
    self, feature_kit_id: Optional[int],
    sort_by: Optional[str] = None, descending: bool = False,
    limit: Optional[int] = PAGE_LIMIT, offset: Optional[int] = None
) -> tuple[list[models.Feature], int]:
    
    persist_session = self._session is not None
    if not self._session:
        self.open_session()

    query = self._session.query(models.Feature)

    if feature_kit_id is not None:
        query = query.where(
            models.Feature.feature_kit_id == feature_kit_id
        )

    n_pages: int = math.ceil(query.count() / limit) if limit is not None else 1

    if sort_by is not None:
        attr = getattr(models.Feature, sort_by)
        if descending:
            attr = attr.desc()

        query = query.order_by(attr)

    if offset is not None:
        query = query.offset(offset)

    if limit is not None:
        query = query.limit(limit)

    features = query.all()

    if not persist_session:
        self.close_session()

    return features, n_pages


def delete_feature(
    self, feature_id: int, commit: bool = True
) -> models.Feature:
    persist_session = self._session is not None
    if not self._session:
        self.open_session()

    feature = self._session.get(models.Feature, feature_id)
    self._session.delete(feature)

    if commit:
        self._session.commit()

    if not persist_session:
        self.close_session()

    return feature


def update_feature(
    self, feature: models.Feature, commit: bool = True
) -> models.Feature:
    persist_session = self._session is not None
    if not self._session:
        self.open_session()

    self._session.add(feature)
    if commit:
        self._session.commit()
        self._session.refresh(feature)

    if not persist_session:
        self.close_session()

    return feature

    