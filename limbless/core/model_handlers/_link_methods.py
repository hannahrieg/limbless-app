import math
from typing import Optional, Union

from sqlalchemy.orm import selectinload
from sqlmodel import and_

from ... import models, logger, categories
from .. import exceptions


def get_sample_libraries(self, sample_id: int) -> list[models.Library]:
    persist_session = self._session is not None
    if not self._session:
        self.open_session()

    if self._session.get(models.Sample, sample_id) is None:
        raise exceptions.ElementDoesNotExist(f"Sample with id {sample_id} does not exist")

    sample_libraries = self._session.query(models.Sample).join(
        models.Library,
        models.Library.sample_id == models.Sample.id
    ).all()

    if not persist_session:
        self.close_session()

    return sample_libraries


def get_project_data(
    self, project_id: int,
    unraveled: bool = False
) -> Union[list[models.Sample], list[tuple[models.Sample, models.Library]]]:
    persist_session = self._session is not None
    if not self._session:
        self.open_session()

    if self._session.get(models.Project, project_id) is None:
        raise exceptions.ElementDoesNotExist(f"Project with id {project_id} does not exist")

    if not unraveled:
        project_data = self._session.query(models.Sample).where(
            models.Sample.project_id == project_id
        ).options(selectinload(models.Sample.libraries)).all()
    else:
        project_data = self._session.query(models.Sample, models.Library).join(
            models.LibrarySampleLink, models.Sample.id == models.LibrarySampleLink.sample_id
        ).join(
            models.Library, models.LibrarySampleLink.library_id == models.Library.id
        ).where(
            models.Sample.project_id == project_id
        ).all()

    if not persist_session:
        self.close_session()
    return project_data


def get_lanes_in_experiment(
    self, experiment_id: int
) -> dict[int, list[int]]:
    
    persist_session = self._session is not None
    if not self._session:
        self.open_session()

    if (_ := self._session.get(models.Experiment, experiment_id)) is None:
        raise exceptions.ElementDoesNotExist(f"Experiment with id {experiment_id} does not exist")
    
    data = self._session.query(
        models.ExperimentLibraryLink.library_id,
        models.ExperimentLibraryLink.lane
    ).where(
        models.ExperimentLibraryLink.experiment_id == experiment_id
    ).order_by(models.ExperimentLibraryLink.lane).all()

    lanes: dict[int, list[int]] = {}
    for library_id, lane in data:
        if library_id not in lanes:
            lanes[library_id] = []
        lanes[library_id].append(lane)
    
    if not persist_session:
        self.close_session()

    return lanes


def link_sample_library(
    self, sample_id: int, library_id: int,
    cmo_id: Optional[int] = None,
    commit: bool = True
) -> models.SampleLibraryLink:
    
    persist_session = self._session is not None
    if not self._session:
        self.open_session()

    if (sample := self._session.get(models.Sample, sample_id)) is None:
        raise exceptions.ElementDoesNotExist(f"Sample with id {sample_id} does not exist")
    
    if (library := self._session.get(models.Library, library_id)) is None:
        raise exceptions.ElementDoesNotExist(f"Library with id {library_id} does not exist")
    
    if cmo_id is not None:
        if (_ := self._session.get(models.CMO, cmo_id)) is None:
            raise exceptions.ElementDoesNotExist(f"CMO with id {cmo_id} does not exist")
        
    if self._session.query(models.SampleLibraryLink).where(
        models.SampleLibraryLink.sample_id == sample_id,
        models.SampleLibraryLink.library_id == library_id,
    ).first():
        raise exceptions.LinkAlreadyExists(f"Sample with id {sample_id} and Library with id {library_id} are already linked")
    
    sample_library_link = models.SampleLibraryLink(
        sample_id=sample_id, library_id=library_id, cmo_id=cmo_id,
    )

    self._session.add(sample_library_link)
    sample.num_libraries += 1
    library.num_samples += 1

    if commit:
        self._session.commit()
        self._session.refresh(sample_library_link)

    if not persist_session:
        self.close_session()

    return sample_library_link
    

def link_library_pool(
    self,
    pool_id: int, library_id: int,
    commit: bool = True
) -> models.LibraryPoolLink:

    persist_session = self._session is not None
    if not self._session:
        self.open_session()

    if (pool := self._session.get(models.Pool, pool_id)) is None:
        raise exceptions.ElementDoesNotExist(f"Pool with id {pool_id} does not exist")
    if (library := self._session.get(models.Library, library_id)) is None:
        raise exceptions.ElementDoesNotExist(f"Library with id {library_id} does not exist")
    
    if self._session.query(models.LibraryPoolLink).where(
        and_(
            models.LibraryPoolLink.pool_id == pool_id,
            models.LibraryPoolLink.library_id == library_id,
        )
    ).first():
        raise exceptions.LinkAlreadyExists(f"Library with id {library_id} and pool with id {pool_id} are already linked")

    library_pool_link = models.LibraryPoolLink(
        pool_id=pool_id, library_id=library_id,
    )
    self._session.add(library_pool_link)
    library.num_pools += 1
    pool.num_libraries += 1

    if commit:
        self._session.commit()
        self._session.refresh(library_pool_link)

    if not persist_session:
        self.close_session()

    return library_pool_link


def get_sample_library_links(
    self,
    sample_id: Optional[int] = None,
    library_id: Optional[int] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> tuple[Optional[models.SampleLibraryLink], int]:
    
    persist_session = self._session is not None
    if not self._session:
        self.open_session()

    query = self._session.query(models.SampleLibraryLink)
    if sample_id is not None:
        query = query.where(models.SampleLibraryLink.sample_id == sample_id)

    if library_id is not None:
        query = query.where(models.SampleLibraryLink.library_id == library_id)
    
    n_pages: int = math.ceil(query.count() / limit) if limit is not None else 1

    if limit is not None:
        query = query.limit(limit)
    if offset is not None:
        query = query.offset(offset)

    links = query.all()

    if not persist_session:
        self.close_session()

    return links, n_pages


def link_library_seq_request(
    self, library_id: int, seq_request_id: int,
    commit: bool = True
) -> models.SeqRequestLibraryLink:

    persist_session = self._session is not None
    if not self._session:
        self.open_session()

    if (library := self._session.get(models.Library, library_id)) is None:
        raise exceptions.ElementDoesNotExist(f"Library with id {library_id} does not exist")
    if (seq_request := self._session.get(models.SeqRequest, seq_request_id)) is None:
        raise exceptions.ElementDoesNotExist(f"SeqRequest with id {seq_request_id} does not exist")

    if self._session.query(models.SeqRequestLibraryLink).where(
        models.SeqRequestLibraryLink.library_id == library_id,
        models.SeqRequestLibraryLink.seq_request_id == seq_request_id,
    ).first():
        raise exceptions.LinkAlreadyExists(f"Library with id {library_id} and SeqRequest with id {seq_request_id} are already linked")

    link = models.SeqRequestLibraryLink(
        library_id=library_id, seq_request_id=seq_request_id,
    )
    self._session.add(link)
    seq_request.num_libraries += 1
    library.num_seq_requests += 1
    self._session.add(seq_request)
    self._session.add(library)

    if commit:
        self._session.commit()
        self._session.refresh(link)

    if not persist_session:
        self.close_session()

    return link


def unlink_library_seq_request(
    self, library_id: int, seq_request_id: int,
    commit: bool = True
) -> None:
    
    persist_session = self._session is not None
    if not self._session:
        self.open_session()

    if (library := self._session.get(models.Library, library_id)) is None:
        raise exceptions.ElementDoesNotExist(f"Library with id {library_id} does not exist")
    if (seq_request := self._session.get(models.SeqRequest, seq_request_id)) is None:
        raise exceptions.ElementDoesNotExist(f"SeqRequest with id {seq_request_id} does not exist")
    
    if (links := self._session.query(models.SeqRequestLibraryLink).where(
        models.SeqRequestLibraryLink.library_id == library_id,
        models.SeqRequestLibraryLink.seq_request_id == seq_request_id,
    ).all()) is None:
        raise exceptions.LinkDoesNotExist(f"Library with id {library_id} and SeqRequest with id {seq_request_id} are not linked")
    
    for link in links:
        self._session.delete(link)

    seq_request.num_libraries -= 1
    library.num_seq_requests -= 1
    self._session.add(seq_request)
    self._session.add(library)

    if commit:
        self._session.commit()

    if not persist_session:
        self.close_session()


def link_experiment_library(
    self, experiment_id: int, library_id: int,
    lane: int, commit: bool = True
) -> models.ExperimentLibraryLink:

    persist_session = self._session is not None
    if not self._session:
        self.open_session()

    if (experiment := self._session.get(models.Experiment, experiment_id)) is None:
        raise exceptions.ElementDoesNotExist(f"Experiment with id {experiment_id} does not exist")
    if lane > experiment.num_lanes:
        raise exceptions.InvalidValue(f"Experiment with id {experiment_id} has only {experiment.num_lanes} lanes")
    if (library := self._session.get(models.Library, library_id)) is None:
        raise exceptions.ElementDoesNotExist(f"Library with id {library_id} does not exist")

    if self._session.query(models.ExperimentLibraryLink).where(
        models.ExperimentLibraryLink.experiment_id == experiment_id,
        models.ExperimentLibraryLink.library_id == library_id,
        models.ExperimentLibraryLink.lane == lane,
    ).first():
        raise exceptions.LinkAlreadyExists(f"Experiment with id {experiment_id} and Library with id {library_id} are already linked")

    experiment_library_link = models.ExperimentLibraryLink(
        experiment_id=experiment_id, library_id=library_id, lane=lane,
    )
    self._session.add(experiment_library_link)
    experiment.num_libraries += 1

    if commit:
        self._session.commit()
        self._session.refresh(experiment_library_link)

    if not persist_session:
        self.close_session()

    return experiment_library_link


def unlink_experiment_library(
    self, experiment_id: int, library_id: int, lane: int,
    commit: bool = True
):
    persist_session = self._session is not None
    if not self._session:
        self.open_session()

    if (experiment := self._session.get(models.Experiment, experiment_id)) is None:
        raise exceptions.ElementDoesNotExist(f"Experiment with id {experiment_id} does not exist")
    if (library := self._session.get(models.Library, library_id)) is None:
        raise exceptions.ElementDoesNotExist(f"Library with id {library_id} does not exist")

    if (link := self._session.query(models.ExperimentLibraryLink).where(
        models.ExperimentLibraryLink.experiment_id == experiment_id,
        models.ExperimentLibraryLink.library_id == library_id,
        models.ExperimentLibraryLink.lane == lane,
    ).first()) is None:
        raise exceptions.ElementDoesNotExist(f"Experiment with id {experiment_id} and Library with id {library_id} are not linked")

    self._session.delete(link)
    experiment.num_libraries -= 1
    library.num_experiments -= 1
    if commit:
        self._session.commit()

    if not persist_session:
        self.close_session()
