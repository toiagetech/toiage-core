"""Schemas for signal endpoints."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SignalCreate(BaseModel):
    """Create a single signal for a child."""

    child_id: int = Field(..., description="Child profile ID", examples=[1])
    signal_type: str = Field(
        ...,
        description="play, learning, parent_observation, school, teacher_feedback",
        examples=["play"],
    )
    source: str = Field(..., description="Source system", examples=["app"])
    category: str | None = Field(default=None, description="Sub-category", examples=["puzzle"])
    data: dict[str, Any] = Field(..., description="Signal payload")
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    recorded_at: datetime = Field(..., description="When the observation occurred")


class SignalBulkCreate(BaseModel):
    """Create multiple signals at once."""

    child_id: int = Field(..., description="Child profile ID", examples=[1])
    source: str = Field(..., description="Source system", examples=["app"])
    signals: list[SignalCreate] = Field(..., description="List of signals to create")


class SignalRead(BaseModel):
    """A single signal record."""

    id: int
    child_id: int
    signal_type: str
    source: str
    category: str | None
    data: dict[str, Any]
    confidence: float | None
    processed: bool
    processed_at: datetime | None
    recorded_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}
