import math
from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.sql.operators import or_

from ... import models, PAGE_LIMIT
from ...categories import SeqRequestStatus, FileType, LibraryStatus, DataDeliveryModeEnum, SeqRequestStatusEnum, PoolStatus, DeliveryStatus, ReadTypeEnum, SampleStatus, PoolType, SubmissionTypeEnum
from .. import exceptions


def create_seq_request(
    self, name: str,
    description: Optional[str],
    requestor_id: int,
    billing_contact_id: int,
    data_delivery_mode: DataDeliveryModeEnum,
    read_type: ReadTypeEnum,
    submission_type: SubmissionTypeEnum,
    contact_person_id: int,
    organization_contact_id: int,
    bioinformatician_contact_id: Optional[int] = None,
    read_length: Optional[int] = None,
    num_lanes: Optional[int] = None,
    special_requirements: Optional[str] = None,
    
    billing_code: Optional[str] = None,
) -> models.SeqRequest:

    persist_session = self._session is not None
    if not self._session:
        self.open_session()

    if (requestor := self._session.get(models.User, requestor_id)) is None:
        raise exceptions.ElementDoesNotExist(f"User with id '{requestor_id}', not found.")

    if self._session.get(models.Contact, billing_contact_id) is None:
        raise exceptions.ElementDoesNotExist(f"Contact with id '{billing_contact_id}', not found.")

    if self._session.get(models.Contact, contact_person_id) is None:
        raise exceptions.ElementDoesNotExist(f"Contact with id '{contact_person_id}', not found.")
    
    if self._session.get(models.Contact, organization_contact_id) is None:
        raise exceptions.ElementDoesNotExist(f"Contact with id '{organization_contact_id}', not found.")

    if bioinformatician_contact_id is not None:
        if (bioinformatician_contact := self._session.get(models.Contact, bioinformatician_contact_id)) is None:
            raise exceptions.ElementDoesNotExist(f"Contact with id '{bioinformatician_contact_id}', not found.")
    else:
        bioinformatician_contact = None
        
    seq_request = models.SeqRequest(
        name=name.strip(),
        description=description.strip() if description else None,
        requestor_id=requestor_id,
        read_length=read_length,
        num_lanes=num_lanes,
        read_type_id=read_type.id,
        special_requirements=special_requirements,
        billing_contact_id=billing_contact_id,
        submission_type_id=submission_type.id,
        contact_person_id=contact_person_id,
        organization_contact_id=organization_contact_id,
        bioinformatician_contact_id=bioinformatician_contact_id,
        status_id=SeqRequestStatus.DRAFT.id,
        data_delivery_mode_id=data_delivery_mode.id,
        billing_code=billing_code.strip() if billing_code else None,
    )

    requestor.num_seq_requests += 1

    seq_request.delivery_email_links.append(models.SeqRequestDeliveryEmailLink(
        email=requestor.email,
        status_id=DeliveryStatus.PENDING.id,
    ))
    self._session.add(seq_request)
    self._session.add(requestor)
    self._session.commit()
    self._session.refresh(seq_request)

    if bioinformatician_contact is not None:
        seq_request.delivery_email_links.append(models.SeqRequestDeliveryEmailLink(
            email=bioinformatician_contact.email,
            status_id=DeliveryStatus.PENDING.id,
        ))
        self._session.add(seq_request)
        self._session.commit()
        self._session.refresh(seq_request)

    if not persist_session:
        self.close_session()

    return seq_request


def get_seq_request(self, seq_request_id: int) -> Optional[models.SeqRequest]:
    persist_session = self._session is not None
    if not self._session:
        self.open_session()

    seq_request = self._session.get(models.SeqRequest, seq_request_id)

    if not persist_session:
        self.close_session()
    return seq_request


def get_seq_requests(
    self,
    status_in: Optional[list[SeqRequestStatusEnum]] = None,
    show_drafts: bool = True,
    sort_by: Optional[str] = None, descending: bool = False,
    user_id: Optional[int] = None,
    limit: Optional[int] = PAGE_LIMIT, offset: Optional[int] = None,
) -> tuple[list[models.SeqRequest], int]:

    persist_session = self._session is not None
    if not self._session:
        self.open_session()

    query = self._session.query(models.SeqRequest)

    if user_id is not None:
        query = query.where(
            models.SeqRequest.requestor_id == user_id
        )

    if status_in is not None:
        status_ids = [status.id for status in status_in]
        query = query.where(
            models.SeqRequest.status_id.in_(status_ids)  # type: ignore
        )

    if not show_drafts:
        query = query.where(
            or_(
                models.SeqRequest.status_id != SeqRequestStatus.DRAFT.id,
                models.SeqRequest.requestor_id == user_id
            )
        )

    if sort_by is not None:
        attr = getattr(models.SeqRequest, sort_by)
        if descending:
            attr = attr.desc()

        query = query.order_by(sa.nulls_last(attr))

    n_pages: int = math.ceil(query.count() / limit) if limit is not None else 1

    if offset is not None:
        query = query.offset(offset)

    if limit is not None:
        query = query.limit(limit)

    seq_requests = query.all()

    if not persist_session:
        self.close_session()

    return seq_requests, n_pages


def submit_seq_request(
    self, seq_request_id: int,
    commit: bool = True
) -> models.SeqRequest:
    persist_session = self._session is not None
    if not self._session:
        self.open_session()

    seq_request: models.SeqRequest
    if (seq_request := self._session.get(models.SeqRequest, seq_request_id)) is None:
        raise exceptions.ElementDoesNotExist(f"SeqRequest with id '{seq_request}', not found.")

    seq_request.status_id = SeqRequestStatus.SUBMITTED.id
    seq_request.timestamp_submitted_utc = datetime.now()
    for library in seq_request.libraries:
        if library.status == LibraryStatus.DRAFT:
            library.status_id = LibraryStatus.SUBMITTED.id
            self._session.add(library)

    for sample in seq_request.samples:
        if sample.status == SampleStatus.DRAFT:
            sample.status_id = SampleStatus.SUBMITTED.id
            self._session.add(sample)

    for pool in seq_request.pools:
        pool.status_id = PoolStatus.SUBMITTED.id
        self._session.add(pool)

    if commit:
        self._session.commit()
        self._session.refresh(seq_request)

    if not persist_session:
        self.close_session()

    return seq_request


def update_seq_request(
    self, seq_request: models.SeqRequest,
    commit: bool = True
) -> models.SeqRequest:
    persist_session = self._session is not None
    if not self._session:
        self.open_session()

    self._session.add(seq_request)

    if commit:
        self._session.commit()
        self._session.refresh(seq_request)
        self._session.refresh(seq_request.billing_contact)
        self._session.refresh(seq_request.contact_person)
        if seq_request.bioinformatician_contact_id is not None:
            self._session.refresh(seq_request.bioinformatician_contact)

    if not persist_session:
        self.close_session()

    return seq_request


def delete_seq_request(self, seq_request_id: int) -> None:
    persist_session = self._session is not None
    if not self._session:
        self.open_session(autoflush=False)

    if (seq_request := self._session.get(models.SeqRequest, seq_request_id)) is None:
        raise exceptions.ElementDoesNotExist(f"SeqRequest with id {seq_request_id} does not exist")

    for library in seq_request.libraries:
        self.delete_library(library.id)

    for pool in seq_request.pools:
        if pool.type == PoolType.EXTERNAL:
            self.delete_pool(pool.id)

    seq_request.requestor.num_seq_requests -= 1
    self._session.delete(seq_request)
    self._session.commit()

    if not persist_session:
        self.close_session()


def query_seq_requests(
    self, word: str,
    user_id: Optional[int] = None,
    status_in: Optional[list[SeqRequestStatusEnum]] = None,
    limit: Optional[int] = PAGE_LIMIT,
) -> list[models.SeqRequest]:
    persist_session = self._session is not None
    if not self._session:
        self.open_session()

    query = self._session.query(models.SeqRequest)

    if user_id is not None:
        query = query.where(
            models.SeqRequest.requestor_id == user_id
        )

    if status_in is not None:
        status_ids = [status.id for status in status_in]
        query = query.where(
            models.SeqRequest.status_id.in_(status_ids)
        )

    query = query.order_by(
        sa.func.similarity(models.SeqRequest.name, word).desc()
    )

    if limit is not None:
        query = query.limit(limit)

    seq_requests = query.all()

    if not persist_session:
        self.close_session()
    return seq_requests


def add_file_to_seq_request(
    self, seq_request_id: int, file_id: int
) -> models.SeqRequest:
    persist_session = self._session is not None
    if not self._session:
        self.open_session()

    if (seq_request := self._session.get(models.SeqRequest, seq_request_id)) is None:
        raise exceptions.ElementDoesNotExist(f"SeqRequest with id '{seq_request_id}', not found.")

    if (file := self._session.get(models.File, file_id)) is None:
        raise exceptions.ElementDoesNotExist(f"File with id '{file_id}', not found.")
    
    if file.type == FileType.SEQ_AUTH_FORM:
        if seq_request.seq_auth_form_file_id is not None:
            raise exceptions.LinkAlreadyExists("SeqRequest already has a Seq Auth Form file linked.")
        seq_request.seq_auth_form_file_id = file_id
        self._session.add(seq_request)

    seq_request.files.append(file)

    self._session.commit()
    self._session.refresh(seq_request)

    if not persist_session:
        self.close_session()

    return seq_request


def remove_comment_from_seq_request(self, seq_request_id: int, comment_id: int, commit: bool = True) -> None:
    persist_session = self._session is not None
    if not self._session:
        self.open_session()

    if (seq_request := self._session.get(models.SeqRequest, seq_request_id)) is None:
        raise exceptions.ElementDoesNotExist(f"SeqRequest with id '{seq_request_id}', not found.")

    if (comment := self._session.get(models.Comment, comment_id)) is None:
        raise exceptions.ElementDoesNotExist(f"Comment with id '{comment_id}', not found.")
    
    seq_request.comments.remove(comment)
    self._session.add(seq_request)

    if commit:
        self._session.commit()

    if not persist_session:
        self.close_session()
    return None


def remove_file_from_seq_request(self, seq_request_id: int, file_id: int, commit: bool = True) -> None:
    persist_session = self._session is not None
    if not self._session:
        self.open_session()

    if (seq_request := self._session.get(models.SeqRequest, seq_request_id)) is None:
        raise exceptions.ElementDoesNotExist(f"SeqRequest with id '{seq_request_id}', not found.")

    if (file := self._session.get(models.File, file_id)) is None:
        raise exceptions.ElementDoesNotExist(f"File with id '{file_id}', not found.")
    
    seq_request.files.remove(file)
    
    comments = self._session.query(models.Comment).where(
        models.Comment.file_id == file_id
    ).all()

    for comment in comments:
        self.remove_comment_from_seq_request(seq_request_id, comment.id, commit=False)

    self._session.add(seq_request)

    if commit:
        self._session.commit()

    if not persist_session:
        self.close_session()
    return None


def add_seq_request_share_email(self, seq_request_id: int, email: str) -> models.SeqRequest:
    persist_session = self._session is not None
    if not self._session:
        self.open_session()

    seq_request: models.SeqRequest
    if (seq_request := self._session.get(models.SeqRequest, seq_request_id)) is None:
        raise exceptions.ElementDoesNotExist(f"SeqRequest with id '{seq_request_id}', not found.")
    
    if self._session.query(models.SeqRequestDeliveryEmailLink).where(
        models.SeqRequestDeliveryEmailLink.seq_request_id == seq_request_id,
        models.SeqRequestDeliveryEmailLink.email == email
    ).first() is not None:
        raise exceptions.LinkAlreadyExists(f"SeqRequest with id '{seq_request_id}' already has a share link with email '{email}'.")

    seq_request.delivery_email_links.append(models.SeqRequestDeliveryEmailLink(
        email=email, status_id=DeliveryStatus.PENDING.id
    ))

    self._session.add(seq_request)
    self._session.commit()
    self._session.refresh(seq_request)

    if not persist_session:
        self.close_session()

    return seq_request


def remove_seq_request_share_email(self, seq_request_id: int, email: str) -> models.SeqRequest:
    persist_session = self._session is not None
    if not self._session:
        self.open_session()

    seq_request: models.SeqRequest
    if (seq_request := self._session.get(models.SeqRequest, seq_request_id)) is None:
        raise exceptions.ElementDoesNotExist(f"SeqRequest with id '{seq_request_id}', not found.")
    
    if (delivery_link := self._session.query(models.SeqRequestDeliveryEmailLink).where(
        models.SeqRequestDeliveryEmailLink.seq_request_id == seq_request_id,
        models.SeqRequestDeliveryEmailLink.email == email
    ).first()) is None:
        raise exceptions.ElementDoesNotExist(f"Share link with '{email}', not found.")

    seq_request.delivery_email_links.remove(delivery_link)
    self._session.delete(delivery_link)
    self._session.add(seq_request)
    self._session.commit()
    self._session.refresh(seq_request)

    if not persist_session:
        self.close_session()
    return seq_request


def process_seq_request(self, seq_request_id: int, status: SeqRequestStatusEnum) -> models.SeqRequest:
    persist_session = self._session is not None
    if not self._session:
        self.open_session()

    if (seq_request := self._session.get(models.SeqRequest, seq_request_id)) is None:
        raise exceptions.ElementDoesNotExist(f"SeqRequest with id '{seq_request_id}', not found.")

    seq_request.status_id = status.id
    
    if status == SeqRequestStatus.ACCEPTED:
        sample_status = SampleStatus.ACCEPTED
        library_status = LibraryStatus.ACCEPTED
        pool_status = PoolStatus.ACCEPTED
    elif status == SeqRequestStatus.DRAFT:
        sample_status = SampleStatus.DRAFT
        library_status = LibraryStatus.DRAFT
        pool_status = PoolStatus.DRAFT
    elif status == SeqRequestStatus.REJECTED:
        sample_status = SampleStatus.REJECTED
        library_status = LibraryStatus.REJECTED
        pool_status = PoolStatus.REJECTED
    else:
        raise TypeError(f"Cannot process request to '{status}'.")
    
    for sample in seq_request.samples:
        sample.status_id = sample_status.id
        if sample_status != SampleStatus.ACCEPTED:
            continue
        
        is_prepared = True
        for library_link in sample.library_links:
            if library_link.library.pool_id is None:
                is_prepared = False
                break
        if is_prepared:
            sample.status_id = SampleStatus.PREPARED.id

    for library in seq_request.libraries:
        library.status_id = library_status.id
        if library_status != LibraryStatus.ACCEPTED:
            continue
        
        if library.pool_id is not None:
            library.status_id = LibraryStatus.POOLED.id

    for pool in seq_request.pools:
        pool.status_id = pool_status.id

    self._session.add(seq_request)
    self._session.commit()
    self._session.refresh(seq_request)

    if not persist_session:
        self.close_session()

    return seq_request