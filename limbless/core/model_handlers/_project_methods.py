from typing import Optional, Union

from ... import models, logger
from .. import exceptions
from ...categories import UserResourceRelation


def create_project(
    self, name: str, description: str, owner_id: int
) -> models.Project:
    persist_session = self._session is not None
    if not self._session:
        self.open_session()

    if self._session.get(models.User, owner_id) is None:
        raise exceptions.ElementDoesNotExist(f"User with id {owner_id} does not exist")

    project = models.Project(
        name=name,
        description=description,
        owner_id=owner_id
    )

    self._session.add(project)
    self._session.commit()
    self._session.refresh(project)

    if not persist_session:
        self.close_session()
        
    return project


def get_project(self, project_id: int) -> models.Project:
    persist_session = self._session is not None
    if not self._session:
        self.open_session()

    res = self._session.get(models.Project, project_id)
    if not persist_session:
        self.close_session()
    return res


def get_projects(
    self, limit: Optional[int] = 20, offset: Optional[int] = None,
    sort_by: Optional[str] = None, reversed: bool = False,
    user_id: Optional[int] = None
) -> list[models.Project]:
    persist_session = self._session is not None
    if not self._session:
        self.open_session()

    query = self._session.query(models.Project)

    if user_id is not None:
        query = query.where(
            models.Project.owner_id == user_id
        )

    if sort_by is not None:
        attr = getattr(models.Project, sort_by)
        if reversed:
            attr = attr.desc()
        query = query.order_by(attr)

    if offset is not None:
        query = query.offset(offset)

    if limit is not None:
        query = query.limit(limit)

    projects = query.all()

    for project in projects:
        project._num_samples = len(project.samples)

    if not persist_session:
        self.close_session()
    return projects


def get_num_projects(self, user_id: Optional[int] = None) -> int:
    persist_session = self._session is not None
    if not self._session:
        self.open_session()

    query = self._session.query(models.Project)
    if user_id is not None:
        query = query.where(
            models.Project.owner_id == user_id
        )

    res = query.count()

    if not persist_session:
        self.close_session()
    return res


def delete_project(
    self, project_id: int,
    commit: bool = True
) -> None:
    persist_session = self._session is not None
    if not self._session:
        self.open_session()

    project = self._session.get(models.Project, project_id)
    if not project:
        raise exceptions.ElementDoesNotExist(f"Project with id {project_id} does not exist")

    self._session.delete(project)
    if commit:
        self._session.commit()

    if not persist_session:
        self.close_session()


def update_project(
    self, project_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    commit: bool = True
) -> models.Project:
    persist_session = self._session is not None
    if not self._session:
        self.open_session()

    project = self._session.get(models.Project, project_id)
    if not project:
        raise exceptions.ElementDoesNotExist(f"Project with id {project_id} does not exist")

    if name is not None:
        project.name = name
    if description is not None:
        project.description = description

    if commit:
        self._session.commit()
        self._session.refresh(project)

    if not persist_session:
        self.close_session()
    return project


def project_contains_sample_with_name(
    self, project_id: int, sample_name: str
) -> bool:
    persist_session = self._session is not None
    if not self._session:
        self.open_session()

    project = self._session.get(models.Project, project_id)
    if not project:
        raise exceptions.ElementDoesNotExist(f"Project with id {project_id} does not exist")

    res = self._session.query(models.Sample).where(
        models.Sample.name == sample_name
    ).where(
        models.Sample.project_id == project_id
    ).first() is not None

    if not persist_session:
        self.close_session()
    return res
