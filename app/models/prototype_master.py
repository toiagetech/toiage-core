"""PrototypeMaster model — tracks physical prototype builds for science projects."""

from datetime import datetime

from sqlmodel import Field, SQLModel


class PrototypeMaster(SQLModel, table=True):
    """Master record for a physical prototype build."""
    __tablename__ = "prototype_master"

    id: int | None = Field(default=None, primary_key=True)
    project_id: str = Field(default="", description="Reference to the science project", index=True)
    name: str = Field(nullable=False, description="Prototype name")
    description: str = Field(default="", description="Description of the prototype")
    status: str = Field(default="PLANNED", description="Status: PLANNED, MATERIAL_PENDING, IN_PROGRESS, COMPLETED, FAILED, NEEDS_REVISION")
    assigned_to: str = Field(default="", description="Who is building this prototype")
    cost_sheets: str = Field(default="[]", description="JSON array of cost sheet entries")
    build_records: str = Field(default="[]", description="JSON array of build records")
    notes: str = Field(default="[]", description="JSON array of notes")
    materials: str = Field(default="[]", description="JSON array of materials used")
    total_cost_rs: float = Field(default=0.0, description="Total cost tracked")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)