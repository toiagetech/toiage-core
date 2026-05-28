"""Curriculum Master model — stores CBSE curriculum metadata (class, subject, chapter, topic)."""

from datetime import datetime

from sqlmodel import Field, SQLModel


class CurriculumMaster(SQLModel, table=True):
    """Master table for CBSE curriculum data."""
    __tablename__ = "curriculum_master"

    id: int | None = Field(default=None, primary_key=True)
    grade: int = Field(nullable=False, index=True, description="CBSE class grade (6, 7, 8)")
    subject: str = Field(nullable=False, index=True, description="Subject name (Physics, Chemistry, Biology)")
    chapter: str = Field(nullable=False, description="Chapter name")
    topic: str = Field(nullable=False, description="Topic name within the chapter")
    difficulty: str = Field(default="medium", description="Difficulty level of the topic")
    description: str = Field(default="", description="Brief description of the topic")
    prerequisites: str = Field(default="", description="Prerequisite topics, comma-separated")
    estimated_hours: float = Field(default=1.0, description="Estimated teaching hours")
    is_active: bool = Field(default=True, description="Whether this curriculum entry is active")
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)