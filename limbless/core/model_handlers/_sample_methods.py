import math
from typing import Optional

from sqlmodel import and_, func, or_

from ... import models, logger
from .. import exceptions
from ...tools import SearchResult


def create_sample(
    self, name: str,
    organism_tax_id: int,
    owner_id: int,
    project_id: int,
    commit: bool = True
) -> models.Sample:

    persist_session = self._session is not None
    if not self._session:
        self.open_session()

    if (project := self._session.get(models.Project, project_id)) is None:
        raise exceptions.ElementDoesNotExist(f"Project with id '{project_id}', not found.")

    if (organism := self._session.get(models.Organism, organism_tax_id)) is None:
        raise exceptions.ElementDoesNotExist(f"Organism with tax_id '{organism_tax_id}', not found.")
    
    if (user := self._session.get(models.User, owner_id)) is None:
        raise exceptions.ElementDoesNotExist(f"User with id '{owner_id}', not found.")

    sample = models.Sample(
        name=name,
        organism_id=organism.tax_id,
        project_id=project_id,
        owner_id=owner_id
    )

    self._session.add(sample)
    project.num_samples += 1
    user.num_samples += 1
    
    if commit:
        self._session.commit()
        self._session.refresh(sample)

    if not persist_session:
        self.close_session()
    return sample


def get_sample(self, sample_id: int) -> models.Sample:
    persist_session = self._session is not None
    if not self._session:
        self.open_session()

    res = self._session.get(models.Sample, sample_id)

    if not persist_session:
        self.close_session()
    return res


def get_num_samples(
    self, user_id: Optional[int] = None,
    project_id: Optional[int] = None, library_id: Optional[int] = None
) -> int:
    persist_session = self._session is not None
    if not self._session:
        self.open_session()

    query = self._session.query(models.Sample)

    if user_id is not None:
        query = query.where(
            models.Sample.owner_id == user_id
        )

    if project_id is not None:
        query = query.where(
            models.Sample.project_id == project_id
        )

    if library_id is not None:
        query = query.join(
            models.LibrarySampleLink,
            models.Sample.id == models.LibrarySampleLink.sample_id,
            isouter=True
        ).where(
            models.LibrarySampleLink.library_id == library_id
        )

    res = query.count()

    if not persist_session:
        self.close_session()
    return res


def get_samples(
    self, user_id: Optional[int] = None,
    project_id: Optional[int] = None, library_id: Optional[int] = None,
    limit: Optional[int] = 20, offset: Optional[int] = None,
    sort_by: Optional[str] = None, reversed: bool = False,
) -> tuple[list[models.Sample], int]:
    persist_session = self._session is not None
    if not self._session:
        self.open_session()

    query = self._session.query(models.Sample)

    if sort_by is not None:
        attr = getattr(models.Sample, sort_by)
        if reversed:
            attr = attr.desc()
        query = query.order_by(attr)

    if user_id is not None:
        query = query.where(
            models.Sample.owner_id == user_id
        )

    if project_id is not None:
        query = query.where(
            models.Sample.project_id == project_id
        )

    if library_id is not None:
        query = query.join(
            models.LibrarySampleLink,
            models.Sample.id == models.LibrarySampleLink.sample_id,
            isouter=True
        ).where(
            models.LibrarySampleLink.library_id == library_id
        )

    n_pages: int = math.ceil(query.count() / limit) if limit is not None else 1
    
    if offset is not None:
        query = query.offset(offset)

    if limit is not None:
        query = query.limit(limit)

    samples = query.all()

    if not persist_session:
        self.close_session()
        
    return samples, n_pages


def get_user_sample_by_name(self, sample_name: str, user_id: int) -> models.Sample:
    persist_session = self._session is not None
    if not self._session:
        self.open_session()

    if self._session.get(models.User, user_id) is None:
        raise exceptions.ElementDoesNotExist(f"User with id {user_id} does not exist")

    sample = self._session.query(models.Sample).filter_by(
        and_(
            name=sample_name,
            owner_id=user_id
        )
    ).first()
    if not persist_session:
        self.close_session()
    return sample


def update_sample(
    self, sample_id: int,
    name: Optional[str] = None,
    organism_tax_id: Optional[int] = None,
    commit: bool = True
) -> models.Sample:
    persist_session = self._session is not None
    if not self._session:
        self.open_session()

    sample = self._session.get(models.Sample, sample_id)
    if not sample:
        raise exceptions.ElementDoesNotExist(f"Sample with id {sample_id} does not exist")

    if organism_tax_id is not None:
        if (organism := self._session.get(models.Organism, organism_tax_id)) is not None:
            sample.organism_id = organism_tax_id
            sample.organism = organism
        else:
            raise exceptions.ElementDoesNotExist(f"Organism with id {organism_tax_id} does not exist")

    if name is not None:
        sample.name = name

    if commit:
        self._session.commit()
        self._session.refresh(sample)

    if not persist_session:
        self.close_session()
    return sample


def delete_sample(
    self, sample_id: int,
    commit: bool = True
) -> None:
    persist_session = self._session is not None
    if not self._session:
        self.open_session()

    if (sample := self._session.get(models.Sample, sample_id)):
        raise exceptions.ElementDoesNotExist(f"Sample with id {sample_id} does not exist")
    
    sample.user.num_samples -= 1
    sample.project.num_samples -= 1
    self._session.delete(sample)

    if commit:
        self._session.commit()

    if not persist_session:
        self.close_session()


def query_samples(
    self, word: str,
    user_id: Optional[int] = None,
    project_id: Optional[int] = None,
    library_id: Optional[int] = None,
    exclude_library_id: Optional[int] = None,
    limit: Optional[int] = 20
) -> list[models.Sample]:

    persist_session = self._session is not None
    if not self._session:
        self.open_session()

    query = self._session.query(models.Sample)
    
    if user_id is not None:
        query = query.where(
            models.Sample.owner_id == user_id
        )

    if project_id is not None:
        query = query.where(
            models.Sample.project_id == project_id
        )

    if library_id is not None:
        query = query.join(
            models.LibrarySampleLink,
            models.Sample.id == models.LibrarySampleLink.sample_id,
            isouter=True
        ).where(
            models.LibrarySampleLink.library_id == library_id
        )

    if exclude_library_id is not None:
        query = query.join(
            models.LibrarySampleLink,
            models.Sample.id == models.LibrarySampleLink.sample_id,
            isouter=True
        ).where(
            or_(
                models.LibrarySampleLink.library_id != exclude_library_id,
                models.LibrarySampleLink.library_id == None
            )
        )

    query = query.order_by(
        func.similarity(models.Sample.name, word).desc()
    )

    if limit is not None:
        query = query.limit(limit)

    res = query.all()

    if not persist_session:
        self.close_session()

    return res