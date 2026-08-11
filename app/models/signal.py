"""Signal model — raw observations from any source about a child."""

from datetime import datetime

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


class Signal(SQLModel, table=True):
    """A raw observation signal from any source.

    Signals are the atomic inputs to the Child Understanding Engine.
    Every interaction, observation, or data point becomes a signal.
    """

    __tablename__ = "signals"

    id: int | None = Field(default=None, primary_key=True)
    child_id: int = Field(foreign_key="children.id", index=True, nullable=False)

    # ── Signal Classification ────────────────────────────────────────
    signal_type: str = Field(
        nullable=False,
        index=True,
        description="play, learning, parent_observation, school, teacher_feedback",
    )
    source: str = Field(
        nullable=False,
        description="Where this came from (e.g. app, teacher, parent_manual)",
    )
    category: str | None = Field(
        default=None,
        index=True,
        description="Sub-category (e.g. puzzle, reading, behavior)",
    )

    # ── Signal Data ───────────────────────────────────────────────────
    data: dict = Field(sa_column=Column(JSON))
    confidence: float | None = Field(
        default=None,
        description="Source-provided confidence (0.0-1.0), if applicable",
    )

    # ── Processing State ──────────────────────────────────────────────
    processed: bool = Field(default=False, index=True, description="Whether this signal was consumed")
    processed_at: datetime | None = Field(default=None)

    # ── Timestamps ────────────────────────────────────────────────────
    recorded_at: datetime = Field(
        nullable=False,
        description="When the observation actually occurred",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
