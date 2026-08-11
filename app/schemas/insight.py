"""Schemas for child insight endpoints."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class InsightRead(BaseModel):
    """A derived child insight."""

    id: int
    child_id: int
    insight_type: str
    category: str | None
    description: str
    evidence: list[dict[str, Any]] | None
    confidence: float
    is_active: bool
    superseded_by_id: int | None
    expires_at: datetime | None
    generated_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class InsightGenerateRequest(BaseModel):
    """Request to trigger insight generation for a child."""

    child_id: int = Field(..., description="Child profile ID", examples=[1])
    since: datetime | None = Field(
        default=None,
        description="Only process signals after this timestamp",
    )
