"""Schemas for /stories endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class StoryCreate(BaseModel):
    """Request to create a new story."""
    content: str = Field(..., description="The story text content", examples=["Once upon a time, in a magical forest..."])
    age_group: str = Field(..., description="Target age group for the story", examples=["3-5", "6-8", "9-12"])
    theme: str = Field(..., description="Story theme", examples=["friendship", "adventure", "kindness"])
    skills: str = Field(default="", description="Skills developed by this story (comma-separated)", examples=["reading", "empathy", "creativity"])
    difficulty: str = Field(default="beginner", description="Reading difficulty level", examples=["beginner", "intermediate", "advanced"])


class StoryRead(BaseModel):
    """A saved story with metadata."""
    id: int = Field(..., description="Unique story identifier", examples=[1])
    content: str = Field(..., description="The story text content")
    age_group: str = Field(..., description="Target age group", examples=["3-5"])
    theme: str = Field(..., description="Story theme", examples=["friendship"])
    skills: str = Field(default="", description="Skills developed")
    difficulty: str = Field(default="beginner", description="Reading difficulty")
    created_at: datetime = Field(..., description="When the story was created")

    model_config = {"from_attributes": True, "json_schema_extra": {
        "examples": [
            {
                "id": 1,
                "content": "Once upon a time...",
                "age_group": "3-5",
                "theme": "friendship",
                "skills": "reading, empathy",
                "difficulty": "beginner",
                "created_at": "2026-05-22T10:00:00Z",
            }
        ]
    }}