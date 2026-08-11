"""Questionnaire models — templates for parent onboarding and their responses."""

from datetime import datetime
from typing import List

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


class QuestionnaireTemplate(SQLModel, table=True):
    """A reusable questionnaire template for child onboarding.

    Admin-defined questions that parents answer to build the initial
    child context for personalization.
    """

    __tablename__ = "questionnaire_templates"

    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(nullable=False, description="Questionnaire title")
    description: str | None = Field(default=None, description="Purpose of this questionnaire")
    questions: List[dict] = Field(
        sa_column=Column(JSON),
        description="List of question objects: {id, text, type, options, required}",
    )
    is_active: bool = Field(default=True, description="Whether this template is in use")
    version: int = Field(default=1, description="Template version for updates")
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class QuestionnaireResponse(SQLModel, table=True):
    """A parent's answers to a questionnaire for a specific child."""

    __tablename__ = "questionnaire_responses"

    id: int | None = Field(default=None, primary_key=True)
    child_id: int = Field(foreign_key="children.id", index=True, nullable=False)
    parent_id: int = Field(foreign_key="parents.id", index=True, nullable=False)
    template_id: int = Field(foreign_key="questionnaire_templates.id", index=True, nullable=False)
    responses: List[dict] = Field(
        sa_column=Column(JSON),
        description="Ordered answers matching template questions",
    )
    child_context: dict | None = Field(
        default=None,
        sa_column=Column(JSON),
        description="Derived structured context from this response",
    )
    completed_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
