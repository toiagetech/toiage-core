"""Assessment pattern configurations for CBSE exam papers."""

from dataclasses import dataclass


@dataclass
class AssessmentPattern:
    """Defines a standard exam assessment pattern."""
    name: str
    description: str
    total_marks: int
    duration_minutes: int
    mcq_count: int
    mcq_marks: int
    vsa_count: int
    vsa_marks: int
    sa_count: int
    sa_marks: int
    la_count: int
    la_marks: int
    easy_pct: int
    medium_pct: int
    hard_pct: int


ASSESSMENT_PATTERNS: dict[str, AssessmentPattern] = {
    "periodic_test": AssessmentPattern(
        name="Periodic Test",
        description="Short periodic assessment (20 marks, 40 min)",
        total_marks=20,
        duration_minutes=40,
        mcq_count=5, mcq_marks=1,
        vsa_count=3, vsa_marks=2,
        sa_count=2, sa_marks=3,
        la_count=1, la_marks=5,
        easy_pct=30, medium_pct=50, hard_pct=20,
    ),
    "half_yearly": AssessmentPattern(
        name="Half-Yearly Examination",
        description="Mid-term examination (50 marks, 120 min)",
        total_marks=50,
        duration_minutes=120,
        mcq_count=10, mcq_marks=1,
        vsa_count=5, vsa_marks=2,
        sa_count=5, sa_marks=3,
        la_count=3, la_marks=5,
        easy_pct=30, medium_pct=50, hard_pct=20,
    ),
    "annual": AssessmentPattern(
        name="Annual Examination",
        description="Final year examination (80 marks, 180 min)",
        total_marks=80,
        duration_minutes=180,
        mcq_count=10, mcq_marks=1,
        vsa_count=5, vsa_marks=2,
        sa_count=5, sa_marks=3,
        la_count=3, la_marks=5,
        easy_pct=30, medium_pct=50, hard_pct=20,
    ),
    "worksheet_30": AssessmentPattern(
        name="Practice Worksheet (30 marks)",
        description="Practice worksheet with mixed question types",
        total_marks=30,
        duration_minutes=45,
        mcq_count=5, mcq_marks=1,
        vsa_count=3, vsa_marks=2,
        sa_count=3, sa_marks=3,
        la_count=2, la_marks=5,
        easy_pct=40, medium_pct=40, hard_pct=20,
    ),
}


def get_assessment_pattern(name: str) -> AssessmentPattern | None:
    """Get an assessment pattern by name."""
    return ASSESSMENT_PATTERNS.get(name.lower().replace(" ", "_"))


def list_patterns() -> list[str]:
    """List available assessment pattern names."""
    return list(ASSESSMENT_PATTERNS.keys())