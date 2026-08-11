"""Schemas for child development record endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class DevelopmentRecordRead(BaseModel):
    """The current developmental understanding snapshot for a child."""

    id: int
    child_id: int
    current_stage: str | None
    understanding_confidence: float
    strengths: list[str] | None
    gaps: list[str] | None
    interests: list[str] | None
    learning_preferences: list[str] | None
    last_signal_at: datetime | None
    total_signals_processed: int
    last_insight_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DevelopmentRecordUpdate(BaseModel):
    """Update a child's development record."""

    current_stage: str | None = None
    understanding_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    strengths: list[str] | None = None
    gaps: list[str] | None = None
    interests: list[str] | None = None
    learning_preferences: list[str] | None = None
