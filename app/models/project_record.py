"""ScienceProjectRecord model — stores generated science projects in the database."""

from datetime import datetime

from sqlmodel import Field, SQLModel


class ScienceProjectRecord(SQLModel, table=True):
    """A generated science project stored in the database."""
    __tablename__ = "science_project_records"

    id: int | None = Field(default=None, primary_key=True)
    project_title: str = Field(nullable=False)
    subject: str = Field(nullable=False, index=True)
    grade: int = Field(nullable=False, index=True)
    topic: str = Field(nullable=False)
    difficulty: str = Field(nullable=False)
    budget: str = Field(default="low")
    provider: str = Field(default="mock")
    short_description: str = Field(default="")
    curriculum_alignment: str = Field(default="")
    estimated_build_time: str = Field(default="")
    estimated_cost: str = Field(default="")
    overall_difficulty: str = Field(default="medium")
    scientific_principle: str = Field(default="")
    simple_explanation: str = Field(default="")
    adult_supervision_required: bool = Field(default=True)
    response_json: str = Field(default="", description="Full JSON response for complex nested fields")
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)