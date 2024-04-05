from typing import Optional, TYPE_CHECKING, ClassVar

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .Base import Base

from .Links import LanePoolLink
from ..categories import PoolStatus, PoolStatusEnum

if TYPE_CHECKING:
    from .Library import Library
    from .User import User
    from .Experiment import Experiment
    from .SeqRequest import SeqRequest
    from .Lane import Lane


class Pool(Base):
    __tablename__ = "pool"
    id: Mapped[int] = mapped_column(sa.Integer, default=None, primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(64), nullable=False, index=True)
    status_id: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    
    num_m_reads_requested: Mapped[Optional[float]] = mapped_column(sa.Float, default=None, nullable=True)
    avg_library_size: Mapped[Optional[int]] = mapped_column(sa.Integer, default=None, nullable=True)
    original_qubit_concentration: Mapped[Optional[float]] = mapped_column(sa.Float, default=None, nullable=True)
    diluted_qubit_concentration: Mapped[Optional[float]] = mapped_column(sa.Float, default=None, nullable=True)

    num_libraries: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)

    owner_id: Mapped[int] = mapped_column(sa.Integer, sa.ForeignKey("lims_user.id"), nullable=False)
    owner: Mapped["User"] = relationship("User", back_populates="pools", lazy="joined")
    libraries: Mapped[list["Library"]] = relationship("Library", back_populates="pool", lazy="select",)

    lanes: Mapped[list["Lane"]] = relationship("Lane", secondary=LanePoolLink.__tablename__, back_populates="pools", lazy="select")
    
    experiment_id: Mapped[int] = mapped_column(sa.ForeignKey("experiment.id"), nullable=True, default=None)
    experiment: Mapped["Experiment"] = relationship("Experiment", back_populates="pools", lazy="select",)

    seq_request_id: Mapped[Optional[int]] = mapped_column(sa.ForeignKey("seqrequest.id"), nullable=True)
    seq_request: Mapped[Optional["SeqRequest"]] = relationship("SeqRequest", lazy="select")

    contact_name: Mapped[str] = mapped_column(sa.String(128), nullable=False)
    contact_email: Mapped[str] = mapped_column(sa.String(128), nullable=False)
    contact_phone: Mapped[Optional[str]] = mapped_column(sa.String(20), nullable=True)

    sortable_fields: ClassVar[list[str]] = ["id", "name", "owner_id", "num_libraries", "num_m_reads_requested"]

    warning_min_molarity: ClassVar[float] = 1.0
    warning_max_molarity: ClassVar[float] = 5.0
    error_min_molarity: ClassVar[float] = 0.5
    error_max_molarity: ClassVar[float] = 10.0

    @property
    def original_molarity(self) -> Optional[float]:
        if self.avg_library_size is None or self.original_qubit_concentration is None:
            return None
        
        return self.original_qubit_concentration / (self.avg_library_size * 660) * 1_000_000
    
    @property
    def diluted_molarity(self) -> Optional[float]:
        if self.avg_library_size is None or self.diluted_qubit_concentration is None:
            return None
        
        return self.diluted_qubit_concentration / (self.avg_library_size * 660) * 1_000_000
    
    @property
    def qubit_concentration(self) -> Optional[float]:
        if self.diluted_qubit_concentration is not None:
            return self.diluted_qubit_concentration
        return self.original_qubit_concentration
    
    @property
    def molarity(self) -> Optional[float]:
        if self.diluted_qubit_concentration is not None:
            return self.diluted_molarity
        return self.original_molarity

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
        }
    
    @property
    def molarity_color_class(self) -> str:
        if (molarity := self.molarity) is None:
            return ""
        
        if molarity < self.error_min_molarity or self.error_max_molarity < molarity:
            return "cemm-red"
        
        if molarity < self.warning_min_molarity or self.warning_max_molarity < molarity:
            return "cemm-yellow"
        
        return "cemm-green"
    
    @property
    def qubit_concentration_str(self) -> str:
        if (q := self.qubit_concentration) is None:
            return ""
        return f"{q:.2f}"
    
    @property
    def molarity_str(self) -> str:
        if (m := self.molarity) is None:
            return ""
        return f"{m:.2f}"
    
    def search_value(self) -> int:
        return self.id
    
    def search_name(self) -> str:
        return self.name
    
    def search_description(self) -> Optional[str]:
        return ""
    
    def list_library_types(self) -> list[str]:
        return list(set([library.type.abbreviation for library in self.libraries]))
    
    @property
    def status(self) -> PoolStatusEnum:
        return PoolStatus.get(self.status_id)
    
    def is_qced(self) -> bool:
        return self.original_qubit_concentration is not None and self.avg_library_size is not None