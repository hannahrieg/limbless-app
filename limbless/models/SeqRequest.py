from typing import Optional, List

from sqlmodel import Field, SQLModel, Relationship


class SeqRequest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    requestor_id: int = Field(nullable=False, foreign_key="user.id")
    requestor: "User" = Relationship(back_populates="requests", sa_relationship_kwargs={"lazy": "joined"})

    billing_contact_id: int = Field(nullable=False, foreign_key="contact.id")
    billing_contact: "Contact" = Relationship(sa_relationship_kwargs={"lazy": "joined"})