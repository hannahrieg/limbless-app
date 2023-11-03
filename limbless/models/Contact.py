from typing import Optional

from sqlmodel import Field, SQLModel


class Contact(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str = Field(nullable=False, max_length=128)
    organization: Optional[str] = Field(nullable=True, max_length=128)
    email: Optional[str] = Field(nullable=True, max_length=128)
    phone: Optional[str] = Field(nullable=True, max_length=16)
    billing_code: Optional[str] = Field(nullable=True, max_length=32)
    address: Optional[str] = Field(nullable=True, max_length=256)
