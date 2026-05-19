from datetime import datetime

from sqlmodel import Field, SQLModel


class Activity(SQLModel, table=True):
    """Generated hands-on learning activity derived from a story."""

    __tablename__ = "activities"

    id: int | None = Field(default=None, primary_key=True)
    story_id: int | None = Field(default=None, foreign_key="stories.id", index=True)
    title: str = Field(nullable=False)
    materials: str = Field(nullable=False)
    instructions: str = Field(nullable=False)
    challenge_question: str = Field(default="", nullable=False)
    age_group: str = Field(nullable=False, index=True)
    activity_mode: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)