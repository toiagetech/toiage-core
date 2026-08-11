"""Content Journey model — tracks what educational content was shown to each child."""

from datetime import datetime

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


class ContentJourney(SQLModel, table=True):
    """An immutable log of content shown to a child.

    Polymorphic by design: content_type + content_id reference
    whatever content system generated it (stories, activities,
    recommendations, etc.) without hard foreign keys.
    """

    __tablename__ = "content_journey"

    id: int | None = Field(default=None, primary_key=True)
    child_id: int = Field(foreign_key="children.id", index=True, nullable=False)

    # ── Content Reference ─────────────────────────────────────────────
    content_type: str = Field(
        nullable=False,
        index=True,
        description="story, activity, reflection, recommendation, play_companion, growth_journey",
    )
    content_id: int = Field(
        nullable=False,
        index=True,
        description="ID in the respective content table",
    )

    # ── Context ───────────────────────────────────────────────────────
    source: str = Field(
        nullable=False,
        description="education_engine, parent, system",
    )
    content_metadata: dict | None = Field(
        default=None,
        sa_column=Column(JSON),
        description="Extra context (theme, goal, difficulty, etc.)",
    )

    # ── Timestamps ────────────────────────────────────────────────────
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
