from datetime import datetime

from sqlmodel import Field, SQLModel


class Story(SQLModel, table=True):
    """Generated story with metadata for future recommendation systems."""

    __tablename__ = "stories"

    id: int | None = Field(default=None, primary_key=True)
    content: str = Field(nullable=False)
    age_group: str = Field(nullable=False, index=True)
    theme: str = Field(nullable=False, index=True)
    skills: str = Field(default="", nullable=False)
    difficulty: str = Field(default="beginner", nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)