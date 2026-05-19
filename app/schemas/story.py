from datetime import datetime

from pydantic import BaseModel


class StoryCreate(BaseModel):
    content: str
    age_group: str
    theme: str
    skills: str = ""
    difficulty: str = "beginner"


class StoryRead(BaseModel):
    id: int
    content: str
    age_group: str
    theme: str
    skills: str
    difficulty: str
    created_at: datetime

    model_config = {"from_attributes": True}