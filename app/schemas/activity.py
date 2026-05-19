from datetime import datetime

from pydantic import BaseModel


class ActivityGenerateRequest(BaseModel):
    story_id: int | None = None
    story_text: str | None = None
    age_group: str
    activity_mode: str = "household"  # "household" | "toy-kit"


class ActivityGenerateResponse(BaseModel):
    id: int
    title: str
    materials: str
    instructions: str
    challenge_question: str
    age_group: str
    activity_mode: str
    story_id: int | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ActivityRead(BaseModel):
    id: int
    story_id: int | None
    title: str
    materials: str
    instructions: str
    challenge_question: str
    age_group: str
    activity_mode: str
    created_at: datetime

    model_config = {"from_attributes": True}