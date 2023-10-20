from typing import Optional

from ... import models, bcrypt
from .. import exceptions
from ...categories import UserRole


def create_user(
    self, email: str,
    first_name: str,
    last_name: str,
    password: str,
    role: UserRole,
    commit: bool = True
) -> models.User:
    persist_session = self._session is not None
    if not self._session:
        self.open_session()

    if self._session.query(models.User).where(
        models.User.email == email
    ).first() is not None:
        raise exceptions.NotUniqueValue(f"User with email {email} already exists")

    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

    user = models.User(
        email=email,
        first_name=first_name,
        last_name=last_name,
        password=hashed_password,
        role=role.value.id
    )

    self._session.add(user)
    if commit:
        self._session.commit()
        self._session.refresh(user)

    if not persist_session:
        self.close_session()
    return user


def get_user(self, user_id: int) -> models.User:
    
    persist_session = self._session is not None
    if self._session is None:
        self.open_session()

    res = self._session.get(models.User, user_id)

    if not persist_session:
        self.close_session()
        
    return res


def get_user_by_email(self, email: str) -> models.User:
    persist_session = self._session is not None
    if not self._session:
        self.open_session()

    user = self._session.query(models.User).where(
        models.User.email == email
    ).first()
    if not persist_session:
        self.close_session()
    return user


def get_users(
    self, limit: Optional[int] = 20, offset: Optional[int] = None,
    sort_by: Optional[str] = None, reversed: bool = False
) -> list[models.User]:
    persist_session = self._session is not None
    if not self._session:
        self.open_session()

    query = self._session.query(models.User)

    if sort_by is not None:
        attr = getattr(models.User, sort_by)
        if reversed:
            attr = attr.desc()
        query = query.order_by(attr)

    if offset is not None:
        query = query.offset(offset)

    if limit is not None:
        query = query.limit(limit)

    users = query.all()

    if not persist_session:
        self.close_session()
    return users


def get_num_users(self) -> int:
    persist_session = self._session is not None
    if not self._session:
        self.open_session()

    res = self._session.query(models.User).count()
    
    if not persist_session:
        self.close_session()
    return res


def update_user(
    self, user_id: int,
    email: Optional[str] = None,
    password: Optional[str] = None,
    role: Optional[UserRole] = None,
    commit: bool = True
) -> models.User:
    persist_session = self._session is not None
    if not self._session:
        self.open_session()

    user = self._session.get(models.User, user_id)
    if not user:
        raise exceptions.ElementDoesNotExist(f"User with id {user_id} does not exist")

    if email is not None:
        user.email = email
    if password is not None:
        user.password = password
    if role is not None:
        if not models.UserRole.is_valid(role):
            raise exceptions.InvalidRole(f"Invalid role {role}")
        user.role = role

    if commit:
        self._session.commit()
        self._session.refresh(user)

    if not persist_session:
        self.close_session()
    return user


def delete_user(self, user_id: int, commit: bool = True) -> None:
    persist_session = self._session is not None
    if not self._session:
        self.open_session()

    user = self._session.get(models.User, user_id)
    if not user:
        raise exceptions.ElementDoesNotExist(f"User with id {user_id} does not exist")

    self._session.delete(user)

    if commit:
        self._session.commit()

    if not persist_session:
        self.close_session()
