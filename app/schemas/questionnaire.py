"""Schemas for questionnaire endpoints."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ─── Questionnaire Templates ──────────────────────────────────────────


class QuestionCreate(BaseModel):
    """A single question inside a questionnaire template."""

    id: str = Field(..., description="Unique question ID within template", examples=["q1"])
    text: str = Field(..., description="Question text", examples=["What is your child's favorite activity?"])
    type: str = Field(
        ...,
        description="Question type: text, number, single_choice, multi_choice, scale",
        examples=["single_choice"],
    )
    options: list[str] | None = Field(default=None, description="Options for choice questions")
    required: bool = Field(default=True, description="Whether this question must be answered")
    category: str | None = Field(default=None, description="Category for grouping", examples=["interests"])


class QuestionnaireTemplateCreate(BaseModel):
    """Create a new questionnaire template."""

    title: str = Field(..., description="Questionnaire title", examples=["Child Onboarding"])
    description: str | None = Field(default=None, description="Purpose of this questionnaire")
    questions: list[QuestionCreate] = Field(..., description="Ordered list of questions")
    is_active: bool = Field(default=True)


class QuestionnaireTemplateRead(BaseModel):
    """A questionnaire template with questions."""

    id: int
    title: str
    description: str | None
    questions: list[dict[str, Any]]
    is_active: bool
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class QuestionnaireTemplateUpdate(BaseModel):
    """Update a questionnaire template."""

    title: str | None = None
    description: str | None = None
    questions: list[dict[str, Any]] | None = None
    is_active: bool | None = None


# ─── Questionnaire Responses ──────────────────────────────────────────


class QuestionnaireSubmit(BaseModel):
    """Submit answers for a child."""

    child_id: int = Field(..., description="Child profile ID", examples=[1])
    parent_id: int = Field(..., description="Submitting parent's ID", examples=[1])
    template_id: int = Field(..., description="Template being answered", examples=[1])
    responses: list[dict[str, Any]] = Field(
        ...,
        description="Ordered answers matching template question IDs",
        examples=[[{"question_id": "q1", "answer": "Building blocks"}]],
    )


class QuestionnaireResponseRead(BaseModel):
    """A saved questionnaire response."""

    id: int
    child_id: int
    parent_id: int
    template_id: int
    responses: list[dict[str, Any]]
    child_context: dict[str, Any] | None
    completed_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class ChildContextOutput(BaseModel):
    """Structured child context derived from questionnaire responses."""

    age: int | None = None
    grade: str | None = None
    interests: list[str] = Field(default_factory=list)
    parent_goals: list[str] = Field(default_factory=list)
    parent_concerns: list[str] = Field(default_factory=list)
    available_resources: list[str] = Field(default_factory=list)
    learning_style: list[str] = Field(default_factory=list)
    preferred_language: str = "en"
    special_notes: str | None = None
