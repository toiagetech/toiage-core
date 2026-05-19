from datetime import datetime

from sqlmodel import Field, SQLModel


class Upload(SQLModel, table=True):
    """Metadata for uploaded image files."""

    __tablename__ = "uploads"

    id: int | None = Field(default=None, primary_key=True)
    filename: str = Field(nullable=False)
    original_name: str = Field(nullable=False)
    file_size: int = Field(nullable=False)
    mime_type: str = Field(nullable=False)
    url: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)