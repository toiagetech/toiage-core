"""Educational validation checks for generated educational outputs."""

import re
from dataclasses import dataclass, field

from app.utils.logger import get_logger

logger = get_logger("app.validations")

# CBSE grade 6-8 subject mapping
VALID_SUBJECTS = {"science", "physics", "chemistry", "biology", "mathematics", "social studies", "english", "hindi", "sanskrit"}

VALID_DIFFICULTIES = {"easy", "medium", "hard"}
VALID_GRADES = {6, 7, 8}

# Minimum materials needed for a valid project
MIN_MATERIALS_COUNT = 2
MIN_BUILD_STEPS = 2
MIN_QUESTIONS_PER_SECTION = 1


@dataclass
class ValidationResult:
    """Result of an educational validation check."""
    valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class EducationalValidator:
    """Validates educational outputs for quality, safety, and curriculum alignment."""

    def validate_materials(self, materials: list[dict]) -> ValidationResult:
        """Check that materials list is complete and practical."""
        result = ValidationResult()

        if not materials:
            result.valid = False
            result.errors.append("Materials list is empty")
            return result

        if len(materials) < MIN_MATERIALS_COUNT:
            result.warnings.append(f"Only {len(materials)} materials listed — consider adding more")

        for i, mat in enumerate(materials):
            item = mat.get("item", "")
            if not item or len(item.strip()) < 2:
                result.errors.append(f"Material at index {i} has missing or invalid item name")
                result.valid = False

        return result

    def validate_project_complexity(self, grade: int, difficulty: str, total_steps: int, materials_count: int) -> ValidationResult:
        """Check that project complexity is appropriate for the grade level."""
        result = ValidationResult()

        if grade not in VALID_GRADES:
            result.errors.append(f"Invalid grade: {grade}. Must be 6, 7, or 8")
            result.valid = False

        if difficulty not in VALID_DIFFICULTIES:
            result.errors.append(f"Invalid difficulty: {difficulty}. Must be easy, medium, or hard")
            result.valid = False

        # Complexity guardrails
        if grade == 6 and total_steps > 10:
            result.warnings.append(f"Class 6 project with {total_steps} steps may be too complex")

        if grade == 8 and total_steps < 3 and difficulty != "easy":
            result.warnings.append(f"Class 8 project with only {total_steps} steps may be too simple for {difficulty} difficulty")

        if materials_count < MIN_MATERIALS_COUNT:
            result.warnings.append(f"Only {materials_count} materials — projects need at least {MIN_MATERIALS_COUNT}")

        return result

    def validate_question_paper(self, questions: list[dict], total_marks: int) -> ValidationResult:
        """Check that question papers have proper structure and marks distribution."""
        result = ValidationResult()

        if not questions:
            result.errors.append("No questions in paper")
            result.valid = False
            return result

        calculated_marks = sum(q.get("marks", 0) for q in questions)
        if calculated_marks != total_marks:
            result.warnings.append(
                f"Question marks sum ({calculated_marks}) doesn't match declared total ({total_marks})"
            )

        for q in questions:
            text = q.get("question_text", "")
            if not text or len(text.strip()) < 5:
                result.errors.append(f"Question {q.get('question_number', '?')} has no valid text")
                result.valid = False

            options = q.get("options")
            if options:
                valid_options = all(
                    options.get(k, "").strip()
                    for k in ["A", "B", "C", "D"]
                )
                if not valid_options:
                    result.errors.append(f"Question {q.get('question_number', '?')} has incomplete options")
                    result.valid = False

                correct = q.get("correct_answer", "")
                if correct not in {"A", "B", "C", "D"}:
                    result.errors.append(f"Question {q.get('question_number', '?')} has invalid correct answer")
                    result.valid = False

        return result

    def validate_difficulty_balance(self, questions: list[dict], easy_pct: int, medium_pct: int, hard_pct: int) -> ValidationResult:
        """Check that difficulty distribution matches the exam blueprint."""
        result = ValidationResult()

        total = easy_pct + medium_pct + hard_pct
        if total != 100:
            result.errors.append(f"Difficulty percentages sum to {total}, must be 100")
            result.valid = False

        if not questions:
            return result

        diff_counts = {"easy": 0, "medium": 0, "hard": 0}
        for q in questions:
            d = q.get("difficulty", "medium").lower()
            if d in diff_counts:
                diff_counts[d] += 1

        total_q = len(questions)
        if total_q > 0:
            actual_easy = (diff_counts["easy"] / total_q) * 100
            if abs(actual_easy - easy_pct) > 20:
                result.warnings.append(
                    f"Easy questions ({actual_easy:.0f}%) deviate significantly from target ({easy_pct}%)"
                )

        return result

    def validate_grade_difficulty(self, grade: int, difficulty: str) -> ValidationResult:
        """Check that difficulty level is appropriate for the grade."""
        result = ValidationResult()

        grade_difficulty_map = {
            6: {"easy", "medium"},
            7: {"easy", "medium", "hard"},
            8: {"medium", "hard"},
        }

        allowed = grade_difficulty_map.get(grade, set())
        if allowed and difficulty not in allowed:
            result.warnings.append(
                f"Difficulty '{difficulty}' may not be appropriate for Class {grade}"
            )

        return result


# Singleton instance
validator = EducationalValidator()