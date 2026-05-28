"""Grade-level rules and configurations for CBSE classes 6-8."""

from dataclasses import dataclass, field


@dataclass
class GradeRule:
    """Rules for a specific CBSE grade level."""
    grade: int
    age_range: str
    description: str
    allowed_difficulties: list[str]
    max_project_steps: int
    min_project_steps: int
    typical_assessment_marks: int
    typical_exam_duration_minutes: int


# Grade rules for CBSE classes 6-8
GRADE_RULES: dict[int, GradeRule] = {
    6: GradeRule(
        grade=6,
        age_range="11-12 years",
        description="CBSE Class 6 — Foundational middle school",
        allowed_difficulties=["easy", "medium"],
        max_project_steps=8,
        min_project_steps=3,
        typical_assessment_marks=50,
        typical_exam_duration_minutes=120,
    ),
    7: GradeRule(
        grade=7,
        age_range="12-13 years",
        description="CBSE Class 7 — Intermediate middle school",
        allowed_difficulties=["easy", "medium", "hard"],
        max_project_steps=12,
        min_project_steps=3,
        typical_assessment_marks=60,
        typical_exam_duration_minutes=150,
    ),
    8: GradeRule(
        grade=8,
        age_range="13-14 years",
        description="CBSE Class 8 — Advanced middle school",
        allowed_difficulties=["medium", "hard"],
        max_project_steps=15,
        min_project_steps=4,
        typical_assessment_marks=80,
        typical_exam_duration_minutes=180,
    ),
}


def get_grade_rule(grade: int) -> GradeRule | None:
    """Get the grade rule for a given CBSE class."""
    return GRADE_RULES.get(grade)


def get_valid_grades() -> list[int]:
    """Get list of supported grade levels."""
    return sorted(GRADE_RULES.keys())