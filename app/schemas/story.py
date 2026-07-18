"""Schemas for /stories endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


# ── Parent-selected generation flow (new) ───────────────────────────


class StoryGenerateRequest(BaseModel):
    """Request to generate a personalized AI story.

    The parent selects these values in the UI before generating a story.
    The backend uses them (along with the saved child profile) to generate
    a personalized story.
    """
    goal: str = Field(..., description="The learning goal/value the story should teach", examples=["friendship"])
    story_mood: str = Field(..., alias="storyMood", description="The mood of the story", examples=["bedtime"])
    story_length: str = Field(..., alias="storyLength", description="The length of the story", examples=["short"])
    theme: str = Field(..., description="The theme/setting of the story", examples=["forest"])
    today_context: str | None = Field(default=None, alias="todayContext", description="Optional context about the child's day", examples=["Aria was feeling lonely because her best friend did not play with her today."])

    # Optional: link to a child profile for personalization
    child_id: int | None = Field(default=None, alias="childId", description="Optional child ID for personalization")

    # LLM options
    provider: str = Field(default="mock", description="LLM provider: mock, openrouter, or deepseek", examples=["mock", "openrouter"])
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature (0.0-2.0)", examples=[0.7, 1.0])
    max_tokens: int = Field(default=1024, ge=1, le=8192, description="Maximum tokens in the response", examples=[100, 1024])

    model_config = {"populate_by_name": True}


class StoryGenerateResponse(BaseModel):
    """Response for the generated-and-saved story."""
    id: int = Field(..., description="Unique story identifier", examples=[1])
    title: str | None = Field(default=None, description="Generated story title")
    content: str = Field(..., description="The story text content")
    goal: str | None = Field(default=None, description="Learning goal")
    story_mood: str | None = Field(default=None, alias="storyMood", description="Story mood")
    story_length: str | None = Field(default=None, alias="storyLength", description="Story length")
    theme: str = Field(..., description="Story theme/setting")
    today_context: str | None = Field(default=None, alias="todayContext", description="Today's context")
    created_at: datetime = Field(..., alias="created_at", description="When the story was created")
    provider: str = Field(..., description="The LLM provider that generated the story", examples=["mock", "openrouter"])
    model: str = Field(..., description="The model that generated the story", examples=["mock-model-v1"])

    model_config = {"from_attributes": True, "populate_by_name": True, "json_schema_extra": {
        "examples": [
            {
                "id": 1,
                "title": "Aria and the Forest Friends",
                "content": "Once upon a time, in a bright green forest...",
                "goal": "friendship",
                "storyMood": "bedtime",
                "storyLength": "short",
                "theme": "forest",
                "todayContext": "Aria was feeling lonely because her best friend did not play with her today.",
                "created_at": "2026-07-18T11:00:00Z",
                "provider": "mock",
                "model": "mock-model-v1",
            }
        ]
    }}


# ── Legacy schemas (kept for backward compatibility) ────────────────


class StoryCreate(BaseModel):
    """Request to create a new story (legacy)."""
    content: str = Field(..., description="The story text content", examples=["Once upon a time, in a magical forest..."])
    age_group: str = Field(..., description="Target age group for the story", examples=["3-5", "6-8", "9-12"])
    theme: str = Field(..., description="Story theme", examples=["friendship", "adventure", "kindness"])
    skills: str = Field(default="", description="Skills developed by this story (comma-separated)", examples=["reading", "empathy", "creativity"])
    difficulty: str = Field(default="beginner", description="Reading difficulty level", examples=["beginner", "intermediate", "advanced"])


class StoryRead(BaseModel):
    """A saved story with metadata (legacy)."""
    id: int = Field(..., description="Unique story identifier", examples=[1])
    title: str | None = Field(default=None, description="Generated story title")
    content: str = Field(..., description="The story text content")
    goal: str | None = Field(default=None, description="Learning goal")
    story_mood: str | None = Field(default=None, alias="storyMood", description="Story mood")
    story_length: str | None = Field(default=None, alias="storyLength", description="Story length")
    theme: str = Field(..., description="Story theme")
    today_context: str | None = Field(default=None, alias="todayContext", description="Today's context")
    age_group: str = Field(default="", description="Target age group (legacy)")
    skills: str = Field(default="", description="Skills developed (legacy)")
    difficulty: str = Field(default="beginner", description="Reading difficulty (legacy)")
    created_at: datetime = Field(..., description="When the story was created")

    model_config = {"from_attributes": True, "populate_by_name": True}