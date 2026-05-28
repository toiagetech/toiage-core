"""Schemas for worksheet generation responses."""

from pydantic import BaseModel, Field

from app.schemas.assessment import (
    FillBlankQuestion,
    MCQQuestion,
    Question,
    ShortAnswerQuestion,
)


class WorksheetSection(BaseModel):
    """A section within a worksheet."""
    section_name: str = Field(..., description="Section name")
    section_type: str = Field(..., description="Type: mcq, fill_blanks, true_false, match, short_answer, long_answer")
    marks_per_question: int = Field(..., description="Marks per question")
    questions: list[MCQQuestion | FillBlankQuestion | Question | ShortAnswerQuestion] = Field(
        default_factory=list, description="Questions in this section"
    )


class WorksheetGenerateRequest(BaseModel):
    """Request to generate a worksheet."""
    grade: int = Field(..., description="CBSE class grade")
    subject: str = Field(..., description="Subject name")
    chapter: str = Field(..., description="Chapter name")
    topic: str = Field(..., description="Topic")
    total_marks: int = Field(default=30, description="Total marks for the worksheet")
    difficulty: str = Field(default="medium")
    provider: str = Field(default="mock")


class WorksheetGenerateResponse(BaseModel):
    """Response for worksheet generation."""
    subject: str = Field(..., description="Subject name")
    grade: int = Field(..., description="CBSE class grade")
    chapter: str = Field(..., description="Chapter name")
    topic: str = Field(..., description="Topic")
    total_marks: int = Field(..., description="Total marks")
    sections: list[WorksheetSection] = Field(default_factory=list, description="Worksheet sections")
    total_time_minutes: str = Field(..., description="Recommended time")
    instructions: list[str] = Field(default_factory=list, description="General instructions")