from dataclasses import dataclass

from .ExtendedEnum import DBEnum, ExtendedEnum


@dataclass(eq=False)
class ProjectStatusEnum(DBEnum):
    description: str
    icon: str

    @property
    def select_name(self) -> str:
        return self.icon
    
    @property
    def display_name(self) -> str:
        return f"{self.name} {self.icon}"


class ProjectStatus(ExtendedEnum[ProjectStatusEnum], enum_type=ProjectStatusEnum):
    DRAFT = ProjectStatusEnum(0, "Draft", "Project has been created but no samples have been submitted for sequencing.", "✍🏼")
    PROCESSING = ProjectStatusEnum(1, "Processing", "Project is being worked on.", "🔬")
    SEQUENCED = ProjectStatusEnum(2, "Sequenced", "All libraries are sequenced.", "🧬")
    DELIVERED = ProjectStatusEnum(3, "Delivered", "Project is completed and data is delivered.", "✅")
    ARCHIVED = ProjectStatusEnum(11, "Archived", "Data is archived.", "🗃️")