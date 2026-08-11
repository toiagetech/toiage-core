"""Schemas for content journey endpoints."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ContentJourneyRead(BaseModel):
    """A single content journey entry."""

    id: int
    child_id: int
    content_type: str
    content_id: int
    source: str
    content_metadata: dict[str, Any] | None
    created_at: datetime

    model_config = {"from_attributes": True}
