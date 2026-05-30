"""AssessmentGenerationHistory model — records each teacher assistant generation call."""

from datetime import datetime

from sqlmodel import Field, SQLModel


class AssessmentGenerationHistory(SQLModel, table=True):
    """Records each generation call with the pattern used and output."""
    __tablename__ = "assessment_generation_history"

    id: int | None = Field(default=None, primary_key=True)
    pattern_id: int | None = Field(default=None, foreign_key="assessment_config.id", index=True)
    grade: int = Field(nullable=False, index=True)
    subject: str = Field(nullable=False)
    chapter: str = Field(default="")
    topic: str = Field(default="")
    question_specs: str = Field(default="", description="JSON of the question specifications used")
    generated_output: str = Field(default="", description="JSON of the generated sections/questions")
    total_marks: int = Field(default=0)
    provider: str = Field(default="mock")
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)