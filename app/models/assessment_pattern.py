"""Assessment Pattern Config model — stores assessment/exam pattern configurations."""

from datetime import datetime

from sqlmodel import Field, SQLModel


class AssessmentConfig(SQLModel, table=True):
    """Configuration for assessment/exam patterns."""
    __tablename__ = "assessment_config"

    id: int | None = Field(default=None, primary_key=True)
    grade: int = Field(nullable=False, index=True, description="CBSE class grade")
    subject: str = Field(nullable=False, description="Subject name")
    pattern_name: str = Field(nullable=False, description="Pattern name (e.g., 'Half-Yearly', 'Annual')")
    total_marks: int = Field(default=80, description="Total marks for the exam")
    duration_minutes: int = Field(default=180, description="Exam duration")
    mcq_count: int = Field(default=10, description="Number of MCQ questions")
    vsa_count: int = Field(default=5, description="Number of very short answer questions")
    sa_count: int = Field(default=5, description="Number of short answer questions")
    la_count: int = Field(default=3, description="Number of long answer questions")
    easy_pct: int = Field(default=30, description="Percentage of easy questions")
    medium_pct: int = Field(default=50, description="Percentage of medium questions")
    hard_pct: int = Field(default=20, description="Percentage of hard questions")
    marks_distribution: str = Field(default="", description="JSON string of marks distribution details")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)