"""Child Development Record model — the central understanding state per child."""

from datetime import datetime

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


class ChildDevelopmentRecord(SQLModel, table=True):
    """The current developmental understanding snapshot for a child.

    Updated as new signals arrive and insights are generated.
    Acts as the single source of truth for all agents.
    """

    __tablename__ = "child_development_records"

    id: int | None = Field(default=None, primary_key=True)
    child_id: int = Field(foreign_key="children.id", index=True, nullable=False, unique=True)

    # ── Understanding State ───────────────────────────────────────────
    current_stage: str | None = Field(
        default=None,
        description="Estimated developmental stage (e.g. early_learner, explorer, thinker)",
    )
    understanding_confidence: float = Field(
        default=0.0,
        description="0.0-1.0 confidence in our understanding of this child",
    )

    # ── Derived Attributes (JSON arrays) ──────────────────────────────
    strengths: list | None = Field(default=None, sa_column=Column(JSON))
    gaps: list | None = Field(default=None, sa_column=Column(JSON))
    interests: list | None = Field(default=None, sa_column=Column(JSON))
    learning_preferences: list | None = Field(default=None, sa_column=Column(JSON))

    # ── Metadata ──────────────────────────────────────────────────────
    last_signal_at: datetime | None = Field(
        default=None,
        description="When the most recent signal was recorded",
    )
    total_signals_processed: int = Field(default=0, description="Cumulative signal count")
    last_insight_at: datetime | None = Field(default=None)

    # ── Timestamps ────────────────────────────────────────────────────
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
