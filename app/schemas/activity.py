"""Schemas for /activities endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class ActivityGenerateRequest(BaseModel):
    """Request to generate a hands-on activity from a story."""
    story_id: int | None = Field(default=None, description="ID of an existing story to base activity on", examples=[1])
    story_text: str | None = Field(default=None, description="Story text to base activity on (use when story_id not provided)", examples=["The brave rabbit explored the magical forest..."])
    age_group: str = Field(..., description="Target age group for the activity", examples=["3-5", "6-8"])
    activity_mode: str = Field(default="household", description="Activity mode: 'household' uses common items, 'toy-kit' uses toys/crafts", examples=["household", "toy-kit"])
    provider: str = Field(default="mock", description="LLM provider: mock, openrouter, or deepseek", examples=["mock", "openrouter"])


class ActivityGenerateResponse(BaseModel):
    """A generated activity with structured fields."""
    id: int = Field(..., description="Unique activity identifier", examples=[1])
    title: str = Field(..., description="Activity title", examples=["Magical Forest Diorama"])
    materials: str = Field(..., description="List of materials needed", examples=["- A shoebox\n- Colored paper\n- Glue\n- Scissors"])
    instructions: str = Field(..., description="Step-by-step instructions", examples=["1. Paint the shoebox...\n2. Cut shapes..."])
    challenge_question: str = Field(..., description="Open-ended question to encourage creativity", examples=["What magical creature would you add?"])
    age_group: str = Field(..., description="Target age group", examples=["3-5"])
    activity_mode: str = Field(default="household", description="Activity mode", examples=["household"])
    story_id: int | None = Field(default=None, description="Source story ID if generated from an existing story", examples=[1])
    created_at: datetime = Field(..., description="When the activity was created")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "title": "Magical Forest Diorama",
                    "materials": "- A shoebox or small cardboard box\n- Colored paper (green, brown, blue)\n- Glue",
                    "instructions": "1. Paint the inside of the shoebox blue for the sky.\n2. Cut tree shapes and glue them inside.",
                    "challenge_question": "What magical creature would you add to your forest?",
                    "age_group": "3-5",
                    "activity_mode": "household",
                    "story_id": 1,
                    "created_at": "2026-05-22T10:00:00Z",
                }
            ]
        },
    }


class ActivityRead(BaseModel):
    """An existing activity with metadata (read-only)."""
    id: int = Field(..., description="Unique activity identifier", examples=[1])
    story_id: int | None = Field(default=None, description="Source story ID", examples=[1])
    title: str = Field(..., description="Activity title")
    materials: str = Field(..., description="List of materials")
    instructions: str = Field(..., description="Step-by-step instructions")
    challenge_question: str = Field(..., description="Open-ended challenge question")
    age_group: str = Field(..., description="Target age group")
    activity_mode: str = Field(default="household", description="Activity mode")
    created_at: datetime = Field(..., description="When the activity was created")

    model_config = {"from_attributes": True}