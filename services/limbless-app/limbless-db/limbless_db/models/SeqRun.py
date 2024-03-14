from sqlmodel import Field, SQLModel

from ..categories import SequencingStatusEnum, SequencingStatus, ReadType, ReadTypeEnum


class SeqRun(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    
    experiment_name: str = Field(nullable=False, max_length=32, unique=True)
    status_id: int = Field(nullable=False)

    run_folder: str = Field(nullable=False, max_length=64)
    flowcell_id: str = Field(nullable=False, max_length=64)
    read_type_id: int = Field(nullable=False)
    rta_version: str = Field(nullable=False, max_length=8)
    recipe_version: str = Field(nullable=False, max_length=8)
    side: str = Field(nullable=False, max_length=8)
    flowcell_mode: str = Field(nullable=False, max_length=8)

    r1_cycles: int = Field(nullable=False)
    r2_cycles: int = Field(nullable=False)
    i1_cycles: int = Field(nullable=False)
    i2_cycles: int = Field(nullable=False)

    @property
    def status(self) -> SequencingStatusEnum:
        return SequencingStatus.get(self.status_id)
    
    @property
    def read_type(self) -> ReadTypeEnum:
        return ReadType.get(self.read_type_id)
    
