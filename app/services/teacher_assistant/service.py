"""Teacher Assistant service — core assessment generation engine for CBSE curriculum."""

from app.schemas.assessment import (
    GenerateAssessmentRequest,
    GenerateAssessmentResponse,
    QuestionSpecItem,
    MCQOption,
    Question,
    ExamSection,
)
from app.services.orchestration.pipeline_runner import orchestrator
from app.utils.logger import get_logger

logger = get_logger("app.teacher_assistant")

VALID_GRADES = {6, 7, 8}


def _validate_grade(grade: int) -> None:
    if grade not in VALID_GRADES:
        raise ValueError(f"Unsupported grade: {grade}. Supported grades: {list(VALID_GRADES)}")


def _difficulty_to_age_group(difficulty: str) -> str:
    mapping = {"easy": "11-12 years", "medium": "12-13 years", "hard": "13-14 years"}
    return mapping.get(difficulty, "12-13 years")


class TeacherAssistantService:
    """Core service for generating educational assessments from teacher-specified patterns."""

    async def generate(self, body: GenerateAssessmentRequest) -> GenerateAssessmentResponse:
        """Generate a custom assessment based on teacher-specified question types and marks."""
        _validate_grade(body.grade)
        age_group = _difficulty_to_age_group(body.difficulty)

        total_marks = sum(spec.count * spec.marks_per_question for spec in body.question_specs)
        question_specs_str = "\n".join(
            f"- {spec.count} x {spec.type} ({spec.marks_per_question} marks each, {spec.difficulty})"
            for spec in body.question_specs
        )

        logger.info(
            "Generating assessment",
            extra={"grade": body.grade, "subject": body.subject, "chapter": body.chapter, "total_marks": total_marks},
        )

        raw = await orchestrator.execute_with_retry(
            category="teacher_assistant",
            prompt_name="custom_assessment",
            variables={
                "grade": str(body.grade),
                "subject": body.subject,
                "chapter": body.chapter,
                "topic": body.topic or body.chapter,
                "difficulty": body.difficulty,
                "question_specs": question_specs_str,
            },
            provider=body.provider,
            max_tokens=4096,
            context=f"Generate assessment for Class {body.grade} {body.subject}: {body.chapter}",
            age_group=age_group,
        )

        data = orchestrator.cleanup_response(raw, expected_fields=["sections"])
        sections = []
        for s in data.get("sections", []):
            questions = []
            for q in s.get("questions", []):
                opts = q.get("options")
                mcq_opts = None
                if opts:
                    mcq_opts = MCQOption(
                        A=opts.get("A", ""),
                        B=opts.get("B", ""),
                        C=opts.get("C", ""),
                        D=opts.get("D", ""),
                    )
                questions.append(
                    Question(
                        question_number=q.get("question_number", 1),
                        question_text=q.get("question_text", ""),
                        options=mcq_opts,
                        correct_answer=q.get("correct_answer"),
                        marks=q.get("marks", s.get("marks_per_question", 1)),
                        difficulty=q.get("difficulty", "medium"),
                        cognitive_level=q.get("cognitive_level", "recall"),
                        chapter=body.chapter,
                        model_explanation=q.get("model_answer"),
                    )
                )
            sections.append(
                ExamSection(
                    section_name=s.get("section_name", ""),
                    marks_per_question=s.get("marks_per_question", 1),
                    total_section_marks=s.get("total_section_marks", sum(q.marks for q in questions)),
                    instructions=s.get("instructions", ""),
                    questions=questions,
                )
            )

        return GenerateAssessmentResponse(
            subject=body.subject,
            grade=body.grade,
            chapter=body.chapter,
            topic=body.topic,
            total_marks=total_marks,
            sections=sections,
            total_time_minutes=data.get("total_time_minutes", f"{total_marks} min"),
            instructions=data.get("instructions", []),
        )


# Singleton instance
teacher_assistant_service = TeacherAssistantService()