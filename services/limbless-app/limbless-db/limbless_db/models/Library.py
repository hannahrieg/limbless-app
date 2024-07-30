from typing import Optional, TYPE_CHECKING, ClassVar
from dataclasses import dataclass
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .Links import LibraryFeatureLink, SampleLibraryLink
from .Base import Base
from .SeqRequest import SeqRequest
from ..categories import LibraryType, LibraryTypeEnum, LibraryStatus, LibraryStatusEnum, GenomeRef, GenomeRefEnum

if TYPE_CHECKING:
    from .Pool import Pool
    from .User import User
    from .IndexKit import IndexKit
    from .Feature import Feature
    from .VisiumAnnotation import VisiumAnnotation
    from .SeqQuality import SeqQuality
    from .File import File
    from .Links import SamplePlateLink
    from .LibraryIndex import LibraryIndex


class Library(Base):
    __tablename__ = "library"

    id: Mapped[int] = mapped_column(sa.Integer, default=None, primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(64), nullable=False)

    type_id: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    status_id: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    genome_ref_id: Mapped[Optional[int]] = mapped_column(sa.Integer, nullable=True, default=None)

    timestamp_stored_utc: Mapped[Optional[datetime]] = mapped_column(sa.DateTime(), nullable=True, default=None)

    seq_depth_requested: Mapped[Optional[float]] = mapped_column(sa.Float, nullable=True, default=None)
    avg_fragment_size: Mapped[Optional[int]] = mapped_column(sa.Float, nullable=True, default=None)
    volume: Mapped[Optional[float]] = mapped_column(sa.Float, nullable=True, default=None)
    qubit_concentration: Mapped[Optional[float]] = mapped_column(sa.Float, nullable=True, default=None)

    num_samples: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    num_features: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)

    ba_report_id: Mapped[Optional[int]] = mapped_column(sa.ForeignKey("file.id"), nullable=True, default=None)
    ba_report: Mapped[Optional["File"]] = relationship("File", lazy="select")

    index_kit_id: Mapped[Optional[int]] = mapped_column(sa.Integer, sa.ForeignKey("index_kit.id"), nullable=True)
    index_kit: Mapped[Optional["IndexKit"]] = relationship("IndexKit", lazy="select")

    pool_id: Mapped[Optional[int]] = mapped_column(sa.ForeignKey("pool.id"), nullable=True)
    pool: Mapped[Optional["Pool"]] = relationship(
        "Pool", back_populates="libraries", lazy="joined", cascade="save-update, merge"
    )

    plate_links: Mapped[list["SamplePlateLink"]] = relationship("SamplePlateLink", back_populates="library", lazy="select")

    owner_id: Mapped[int] = mapped_column(sa.ForeignKey("lims_user.id"), nullable=False)
    owner: Mapped["User"] = relationship("User", back_populates="libraries", lazy="joined")

    sample_links: Mapped[list[SampleLibraryLink]] = relationship(
        SampleLibraryLink, back_populates="library", lazy="select",
        cascade="save-update, merge, delete"
    )

    features: Mapped[list["Feature"]] = relationship("Feature", secondary=LibraryFeatureLink.__tablename__, lazy="select", cascade="save-update, merge")

    seq_request_id: Mapped[int] = mapped_column(sa.ForeignKey("seq_request.id"), nullable=False)
    seq_request: Mapped["SeqRequest"] = relationship("SeqRequest", back_populates="libraries", lazy="select")

    indices: Mapped[list["LibraryIndex"]] = relationship("LibraryIndex", lazy="joined", cascade="all, save-update, merge, delete")

    read_qualities: Mapped[list["SeqQuality"]] = relationship("SeqQuality", back_populates="library", lazy="select", cascade="delete")

    visium_annotation_id: Mapped[Optional[int]] = mapped_column(sa.ForeignKey("visiumannotation.id"), nullable=True, default=None)
    visium_annotation: Mapped[Optional["VisiumAnnotation"]] = relationship("VisiumAnnotation", lazy="select", cascade="all, delete")

    sortable_fields: ClassVar[list[str]] = ["id", "name", "type_id", "status_id", "owner_id", "pool_id", "adapter"]
    
    @property
    def status(self) -> LibraryStatusEnum:
        return LibraryStatus.get(self.status_id)

    @property
    def type(self) -> LibraryTypeEnum:
        return LibraryType.get(self.type_id)
    
    @property
    def genome_ref(self) -> Optional[GenomeRefEnum]:
        if self.genome_ref_id is None:
            return None
        return GenomeRef.get(self.genome_ref_id)
    
    @property
    def qubit_concentration_str(self) -> str:
        if (q := self.qubit_concentration) is None:
            return ""
        return f"{q:.2f}"
    
    @property
    def molarity(self) -> Optional[float]:
        if self.avg_fragment_size is None or self.qubit_concentration is None:
            return None
        return self.qubit_concentration / (self.avg_fragment_size * 660) * 1_000_000
    
    @property
    def molarity_str(self) -> str:
        if (m := self.molarity) is None:
            return ""
        return f"{m:.2f}"
    
    @property
    def timestamp_stored_str(self) -> str:
        return self.timestamp_stored_utc.strftime("%Y-%m-%d %H:%M:%S") if self.timestamp_stored_utc is not None else ""
    
    def is_multiplexed(self) -> bool:
        return self.num_samples > 1
    
    def is_editable(self) -> bool:
        return self.status == LibraryStatus.DRAFT
    
    def is_indexed(self) -> bool:
        return self.is_pooled()
    
    def is_pooled(self) -> bool:
        return self.status == LibraryStatus.POOLED
    
    def __str__(self) -> str:
        return f"Library(id: {self.id}, name: {self.name}, type: {self.type})"
    
    def __repr__(self) -> str:
        return str(self)
    
    def sequences_i7_str(self) -> str:
        i7s = []
        for index in self.indices:
            if index.sequence_i7:
                i7s.append(index.sequence_i7)

        return ", ".join(i7s)
    
    def sequences_i5_str(self) -> str:
        i5s = []
        for index in self.indices:
            if index.sequence_i5:
                i5s.append(index.sequence_i5)

        return ", ".join(i5s)