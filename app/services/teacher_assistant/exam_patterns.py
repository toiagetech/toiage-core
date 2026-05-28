"""Exam pattern generation logic — supports realistic CBSE exam workflows."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ExamPattern:
    """An exam pattern specification."""
    pattern_name: str
    total_marks: int
    duration_minutes: int
    mcq_count: int
    vsa_count: int
    sa_count: int
    la_count: int
    easy_pct: int
    medium_pct: int
    hard_pct: int


@dataclass
class MarksDistribution:
    """Marks distribution across question types."""
    mcq_marks: int = 0
    vsa_marks: int = 0
    sa_marks: int = 0
    la_marks: int = 0
    total: int = 0


class ExamPatternEngine:
    """Builds and balances exam patterns based on CBSE guidelines."""

    # Standard CBSE patterns for classes 6-8
    CBSE_PATTERNS = {
        6: {
            "periodic_test": ExamPattern("Periodic Test", 20, 40, 5, 3, 2, 1, 30, 50, 20),
            "half_yearly": ExamPattern("Half-Yearly", 50, 120, 10, 5, 5, 3, 30, 50, 20),
            "annual": ExamPattern("Annual", 80, 180, 10, 5, 5, 3, 30, 50, 20),
        },
        7: {
            "periodic_test": ExamPattern("Periodic Test", 20, 40, 5, 3, 2, 1, 30, 50, 20),
            "half_yearly": ExamPattern("Half-Yearly", 60, 150, 10, 5, 5, 3, 30, 50, 20),
            "annual": ExamPattern("Annual", 80, 180, 10, 5, 5, 3, 30, 50, 20),
        },
        8: {
            "periodic_test": ExamPattern("Periodic Test", 20, 40, 5, 3, 2, 1, 30, 50, 20),
            "half_yearly": ExamPattern("Half-Yearly", 60, 150, 10, 5, 5, 3, 30, 50, 20),
            "annual": ExamPattern("Annual", 80, 180, 10, 5, 5, 3, 30, 50, 20),
        },
    }

    def build_pattern(
        self,
        grade: int,
        pattern_type: str = "annual",
        mcq_count: Optional[int] = None,
        short_count: Optional[int] = None,
        long_count: Optional[int] = None,
        total_marks: Optional[int] = None,
    ) -> ExamPattern:
        """Build an exam pattern, optionally overriding defaults."""
        grade_patterns = self.CBSE_PATTERNS.get(grade, self.CBSE_PATTERNS[6])
        base = grade_patterns.get(pattern_type, grade_patterns["annual"])

        return ExamPattern(
            pattern_name=base.pattern_name,
            total_marks=total_marks or base.total_marks,
            duration_minutes=base.duration_minutes,
            mcq_count=mcq_count or base.mcq_count,
            vsa_count=5,  # default vsa count
            sa_count=short_count or base.sa_count,
            la_count=long_count or base.la_count,
            easy_pct=base.easy_pct,
            medium_pct=base.medium_pct,
            hard_pct=base.hard_pct,
        )

    def calculate_marks_distribution(self, pattern: ExamPattern) -> MarksDistribution:
        """Calculate marks distribution for an exam pattern."""
        mcq_marks = pattern.mcq_count * 1  # 1 mark each
        vsa_marks = pattern.vsa_count * 2  # 2 marks each
        sa_marks = pattern.sa_count * 3  # 3 marks each
        la_marks = pattern.la_count * 5  # 5 marks each
        total = mcq_marks + vsa_marks + sa_marks + la_marks

        return MarksDistribution(
            mcq_marks=mcq_marks,
            vsa_marks=vsa_marks,
            sa_marks=sa_marks,
            la_marks=la_marks,
            total=total,
        )

    def balance_difficulty(
        self,
        questions: list[dict],
        pattern: ExamPattern,
    ) -> list[dict]:
        """Balance question difficulty to match the exam pattern."""
        if not questions:
            return questions

        total_questions = len(questions)
        if total_questions == 0:
            return questions

        target_easy = int(total_questions * pattern.easy_pct / 100)
        target_medium = int(total_questions * pattern.medium_pct / 100)
        target_hard = total_questions - target_easy - target_medium

        current = {"easy": 0, "medium": 0, "hard": 0}
        for q in questions:
            d = q.get("difficulty", "medium").lower()
            if d in current:
                current[d] += 1

        # Assign difficulties to meet targets
        result = []
        easy_assigned = 0
        medium_assigned = 0
        hard_assigned = 0

        for q in questions:
            d = q.get("difficulty", "medium").lower()
            if d == "easy" and easy_assigned < target_easy:
                result.append(q)
                easy_assigned += 1
            elif d == "hard" and hard_assigned < target_hard:
                result.append(q)
                hard_assigned += 1
            elif medium_assigned < target_medium:
                q["difficulty"] = "medium"
                result.append(q)
                medium_assigned += 1
            elif easy_assigned < target_easy:
                q["difficulty"] = "easy"
                result.append(q)
                easy_assigned += 1
            else:
                q["difficulty"] = "hard"
                result.append(q)
                hard_assigned += 1

        return result


# Singleton instance
exam_pattern_engine = ExamPatternEngine()