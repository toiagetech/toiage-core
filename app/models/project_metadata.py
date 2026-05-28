"""Project Metadata Config model — stores metadata about generated science projects."""

from datetime import datetime

from sqlmodel import Field, SQLModel


class ProjectMetadataConfig(SQLModel, table=True):
    """Configuration and metadata for project generation patterns."""
    __tablename__ = "project_metadata_config"

    id: int | None = Field(default=None, primary_key=True)
    grade: int = Field(nullable=False, index=True, description="CBSE class grade")
    subject: str = Field(nullable=False, description="Subject name")
    topic: str = Field(nullable=False, description="Topic name")
    typical_difficulty: str = Field(default="medium", description="Typical difficulty for this topic")
    typical_materials_count: int = Field(default=5, description="Typical number of materials needed")
    estimated_build_time_minutes: int = Field(default=120, description="Typical build time in minutes")
    estimated_cost_rs: float = Field(default=200.0, description="Typical cost in rupees")
    adult_supervision: bool = Field(default=True, description="Whether adult supervision is typically needed")
    common_materials: str = Field(default="", description="Common materials for this topic, comma-separated")
    safety_notes: str = Field(default="", description="Safety notes for this topic")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)