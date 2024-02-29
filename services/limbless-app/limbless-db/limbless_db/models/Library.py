from typing import Optional, TYPE_CHECKING, ClassVar
from dataclasses import dataclass

from sqlmodel import Field, SQLModel, Relationship

from .Links import LibraryFeatureLink
from .SeqRequest import SeqRequest
from limbless_db.core.categories import LibraryType, LibraryStatus

if TYPE_CHECKING:
    from .Pool import Pool
    from .Links import SampleLibraryLink
    from .CMO import CMO
    from .User import User
    from .IndexKit import IndexKit
    from .Feature import Feature
    from .VisiumAnnotation import VisiumAnnotation
    from .SeqQuality import SeqQuality


@dataclass
class Index:
    sequence: Optional[str]
    adapter: Optional[str]


class Library(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str = Field(nullable=False, max_length=64)
    
    type_id: int = Field(nullable=False)
    status_id: int = Field(nullable=False, default=0)

    volume: Optional[int] = Field(nullable=True, default=None)
    dna_concentration: Optional[float] = Field(nullable=True, default=None)
    total_size: Optional[int] = Field(nullable=True, default=None)

    index_kit_id: Optional[int] = Field(nullable=True, foreign_key="indexkit.id")
    index_kit: Optional["IndexKit"] = Relationship(
        sa_relationship_kwargs={"lazy": "select"}
    )

    pool_id: Optional[int] = Field(nullable=True, foreign_key="pool.id")
    pool: Optional["Pool"] = Relationship(
        back_populates="libraries",
        sa_relationship_kwargs={"lazy": "joined"}
    )

    num_samples: int = Field(nullable=False, default=0)
    num_features: int = Field(nullable=False, default=0)

    owner_id: int = Field(nullable=False, foreign_key="lims_user.id")
    owner: "User" = Relationship(
        back_populates="libraries",
        sa_relationship_kwargs={"lazy": "joined"}
    )

    sample_links: list["SampleLibraryLink"] = Relationship(
        back_populates="library",
        sa_relationship_kwargs={"lazy": "select", "cascade": "delete"}
    )

    cmos: list["CMO"] = Relationship(
        back_populates="library",
        sa_relationship_kwargs={"lazy": "select"}
    )
    features: list["Feature"] = Relationship(
        link_model=LibraryFeatureLink,
        sa_relationship_kwargs={"lazy": "select"}
    )

    seq_request_id: int = Field(nullable=False, foreign_key="seqrequest.id")
    seq_request: "SeqRequest" = Relationship(
        back_populates="libraries",
        sa_relationship_kwargs={"lazy": "select"}
    )

    adapter: Optional[str] = Field(nullable=True, max_length=32)
    index_1_sequence: Optional[str] = Field(nullable=True, max_length=32)
    index_2_sequence: Optional[str] = Field(nullable=True, max_length=32)
    index_3_sequence: Optional[str] = Field(nullable=True, max_length=32)
    index_4_sequence: Optional[str] = Field(nullable=True, max_length=32)

    read_qualities: list["SeqQuality"] = Relationship(
        back_populates="library",
        sa_relationship_kwargs={"lazy": "select", "cascade": "delete"}
    )

    visium_annotation_id: Optional[int] = Field(nullable=True, default=None, foreign_key="visiumannotation.id")
    visium_annotation: Optional["VisiumAnnotation"] = Relationship(
        sa_relationship_kwargs={"lazy": "select", "cascade": "delete"}
    )

    sortable_fields: ClassVar[list[str]] = ["id", "name", "type_id", "owner_id", "pool_id", "adapter"]

    def to_dict(self):
        res = {
            "library_id": self.id,
            "library_name": self.name,
            "library_type": self.type.value,
            "pool": self.pool.name if self.pool is not None else None,
            "adapter": self.adapter,
            "index_1": self.index_1_sequence,
            "index_2": self.index_2_sequence,
            "index_3": self.index_3_sequence,
            "index_4": self.index_4_sequence,
        }

        return res
    
    @property
    def status(self) -> LibraryStatus:
        return LibraryStatus.get(self.status_id)

    @property
    def type(self) -> LibraryType:
        return LibraryType.get(self.type_id)
    
    def is_multiplexed(self) -> bool:
        return self.num_samples > 1
    
    def is_editable(self) -> bool:
        return self.status == LibraryStatus.DRAFT
    
    @property
    def indices(self) -> list[Optional[Index]]:
        return [
            Index(self.index_1_sequence, self.adapter) if self.index_1_sequence is not None else None,
            Index(self.index_2_sequence, self.adapter) if self.index_2_sequence is not None else None,
            Index(self.index_3_sequence, self.adapter) if self.index_3_sequence is not None else None,
            Index(self.index_4_sequence, self.adapter) if self.index_4_sequence is not None else None,
        ]

    def is_indexed(self) -> bool:
        return self.index_1_sequence is not None
    
    def is_pooled(self) -> bool:
        return self.pool_id is not None
    
    def __str__(self) -> str:
        return f"Library(id: {self.id}, name: {self.name}, type: {self.type})"