"""Teacher Assistant service — core assessment generation engine for CBSE curriculum."""

from app.schemas.assessment import (
    MCQGenerateRequest,
    MCQGenerateResponse,
    MCQQuestion,
    MCQOption,
    ShortAnswerGenerateRequest,
    ShortAnswerGenerateResponse,
    ShortAnswerQuestion,
    LongAnswerGenerateRequest,
    LongAnswerGenerateResponse,
    LongAnswerQuestion,
    CustomAssessmentGenerateRequest,
    CustomAssessmentResponse,
    ExamPaperGenerateRequest,
    ExamPaperGenerateResponse,
    ExamSection,
    Question,
    AnswerKey,
    ExamBlueprint,
)
from app.schemas.worksheet import (
    WorksheetGenerateRequest,
    WorksheetGenerateResponse,
    WorksheetSection,
)
from app.services.orchestration.pipeline_runner import orchestrator
from app.utils.logger import get_logger

logger = get_logger("app.teacher_assistant")

VALID_GRADES = {6, 7, 8}
VALID_DIFFICULTIES = {"easy", "medium", "hard"}


def _validate_grade(grade: int) -> None:
    if grade not in VALID_GRADES:
        raise ValueError(f"Unsupported grade: {grade}. Supported grades: {list(VALID_GRADES)}")


def _difficulty_to_age_group(difficulty: str) -> str:
    mapping = {"easy": "11-12 years", "medium": "12-13 years", "hard": "13-14 years"}
    return mapping.get(difficulty, "12-13 years")


class TeacherAssistantService:
    """Core service for generating educational assessments."""

    async def generate_mcq(self, body: MCQGenerateRequest) -> MCQGenerateResponse:
        """Generate multiple-choice questions for a chapter/topic."""
        _validate_grade(body.grade)
        age_group = _difficulty_to_age_group(body.difficulty)

        logger.info(
            "Generating MCQs",
            extra={"grade": body.grade, "subject": body.subject, "chapter": body.chapter, "count": body.question_count},
        )

        raw = await orchestrator.execute_with_retry(
            category="teacher_assistant",
            prompt_name="mcq",
            variables={
                "grade": str(body.grade),
                "subject": body.subject,
                "chapter": body.chapter,
                "topic": body.topic,
                "question_count": str(body.question_count),
                "difficulty": body.difficulty,
            },
            provider=body.provider,
            max_tokens=2048,
            context=f"Generate {body.question_count} MCQs for Class {body.grade} {body.subject}: {body.chapter}",
            age_group=age_group,
        )

        data = orchestrator.cleanup_response(raw, expected_fields=["questions"])
        questions = []
        for q in data.get("questions", []):
            opts = q.get("options", {})
            questions.append(
                MCQQuestion(
                    question_number=q.get("question_number", len(questions) + 1),
                    question_text=q.get("question_text", ""),
                    options=MCQOption(
                        A=opts.get("A", ""),
                        B=opts.get("B", ""),
                        C=opts.get("C", ""),
                        D=opts.get("D", ""),
                    ),
                    correct_answer=q.get("correct_answer", ""),
                    difficulty=q.get("difficulty", body.difficulty),
                    cognitive_level=q.get("cognitive_level", "recall"),
                    explanation=q.get("explanation", ""),
                )
            )

        return MCQGenerateResponse(
            subject=body.subject,
            grade=body.grade,
            chapter=body.chapter,
            topic=body.topic,
            questions=questions,
            total_marks=len(questions),
            time_recommended_minutes=data.get("time_recommended_minutes", f"{body.question_count} min"),
        )

    async def generate_short_answer(self, body: ShortAnswerGenerateRequest) -> ShortAnswerGenerateResponse:
        """Generate short-answer questions for a chapter/topic."""
        _validate_grade(body.grade)
        age_group = _difficulty_to_age_group(body.difficulty)

        logger.info(
            "Generating short-answer questions",
            extra={"grade": body.grade, "subject": body.subject, "chapter": body.chapter},
        )

        raw = await orchestrator.execute_with_retry(
            category="teacher_assistant",
            prompt_name="short_answer",
            variables={
                "grade": str(body.grade),
                "subject": body.subject,
                "chapter": body.chapter,
                "topic": body.topic,
                "question_count": str(body.question_count),
                "difficulty": body.difficulty,
                "marks_per_question": str(body.marks_per_question),
            },
            provider=body.provider,
            max_tokens=2048,
            context=f"Generate {body.question_count} short-answer questions for Class {body.grade} {body.subject}",
            age_group=age_group,
        )

        data = orchestrator.cleanup_response(raw, expected_fields=["questions"])
        questions = []
        for q in data.get("questions", []):
            questions.append(
                ShortAnswerQuestion(
                    question_number=q.get("question_number", len(questions) + 1),
                    question_text=q.get("question_text", ""),
                    marks=q.get("marks", body.marks_per_question),
                    difficulty=q.get("difficulty", body.difficulty),
                    cognitive_level=q.get("cognitive_level", "understanding"),
                    expected_key_points=q.get("expected_key_points", []),
                    model_answer=q.get("model_answer", ""),
                )
            )

        total_marks = sum(q.marks for q in questions)
        return ShortAnswerGenerateResponse(
            subject=body.subject,
            grade=body.grade,
            chapter=body.chapter,
            topic=body.topic,
            questions=questions,
            total_marks=total_marks,
            time_recommended_minutes=data.get("time_recommended_minutes", f"{total_marks * 2} min"),
        )

    async def generate_long_answer(self, body: LongAnswerGenerateRequest) -> LongAnswerGenerateResponse:
        """Generate long-answer questions for a chapter/topic."""
        _validate_grade(body.grade)
        age_group = _difficulty_to_age_group(body.difficulty)

        logger.info(
            "Generating long-answer questions",
            extra={"grade": body.grade, "subject": body.subject, "chapter": body.chapter},
        )

        raw = await orchestrator.execute_with_retry(
            category="teacher_assistant",
            prompt_name="long_answer",
            variables={
                "grade": str(body.grade),
                "subject": body.subject,
                "chapter": body.chapter,
                "topic": body.topic,
                "question_count": str(body.question_count),
                "difficulty": body.difficulty,
                "marks_per_question": str(body.marks_per_question),
            },
            provider=body.provider,
            max_tokens=2048,
            context=f"Generate {body.question_count} long-answer questions for Class {body.grade} {body.subject}",
            age_group=age_group,
        )

        data = orchestrator.cleanup_response(raw, expected_fields=["questions"])
        questions = []
        for q in data.get("questions", []):
            questions.append(
                LongAnswerQuestion(
                    question_number=q.get("question_number", len(questions) + 1),
                    question_text=q.get("question_text", ""),
                    sub_parts=q.get("sub_parts", []),
                    total_marks=q.get("total_marks", body.marks_per_question),
                    difficulty=q.get("difficulty", body.difficulty),
                    cognitive_level=q.get("cognitive_level", "analysis"),
                    expected_key_points=q.get("expected_key_points", []),
                    model_answer=q.get("model_answer", ""),
                )
            )

        total_marks = sum(q.total_marks for q in questions)
        return LongAnswerGenerateResponse(
            subject=body.subject,
            grade=body.grade,
            chapter=body.chapter,
            topic=body.topic,
            questions=questions,
            total_marks=total_marks,
            time_recommended_minutes=data.get("time_recommended_minutes", f"{total_marks * 3} min"),
        )

    async def generate_worksheet(self, body: WorksheetGenerateRequest) -> WorksheetGenerateResponse:
        """Generate a practice worksheet for a chapter/topic."""
        _validate_grade(body.grade)
        age_group = _difficulty_to_age_group(body.difficulty)

        logger.info(
            "Generating worksheet",
            extra={"grade": body.grade, "subject": body.subject, "chapter": body.chapter, "marks": body.total_marks},
        )

        raw = await orchestrator.execute_with_retry(
            category="teacher_assistant",
            prompt_name="worksheet",
            variables={
                "grade": str(body.grade),
                "subject": body.subject,
                "chapter": body.chapter,
                "topic": body.topic,
                "total_marks": str(body.total_marks),
                "difficulty": body.difficulty,
            },
            provider=body.provider,
            max_tokens=3072,
            context=f"Generate worksheet for Class {body.grade} {body.subject}: {body.chapter}",
            age_group=age_group,
        )

        data = orchestrator.cleanup_response(raw, expected_fields=["sections"])
        sections = []
        for s in data.get("sections", []):
            sections.append(
                WorksheetSection(
                    section_name=s.get("section_name", ""),
                    section_type=s.get("section_type", "mcq"),
                    marks_per_question=s.get("marks_per_question", 1),
                    questions=s.get("questions", []),
                )
            )

        return WorksheetGenerateResponse(
            subject=body.subject,
            grade=body.grade,
            chapter=body.chapter,
            topic=body.topic,
            total_marks=body.total_marks,
            sections=sections,
            total_time_minutes=data.get("total_time_minutes", "45 min"),
            instructions=data.get("instructions", []),
        )

    async def generate_custom_assessment(self, body: CustomAssessmentGenerateRequest) -> CustomAssessmentResponse:
        """Generate a custom assessment based on teacher-specified question types and marks."""
        _validate_grade(body.grade)
        age_group = _difficulty_to_age_group(body.difficulty)

        total_marks = sum(spec.count * spec.marks_per_question for spec in body.question_specs)
        question_specs_str = "\n".join(
            f"- {spec.count} x {spec.type} ({spec.marks_per_question} marks each, {spec.difficulty})"
            for spec in body.question_specs
        )

        logger.info(
            "Generating custom assessment",
            extra={"grade": body.grade, "subject": body.subject, "chapter": body.chapter, "total_marks": total_marks},
        )

        raw = await orchestrator.execute_with_retry(
            category="teacher_assistant",
            prompt_name="custom_assessment",
            variables={
                "grade": str(body.grade),
                "subject": body.subject,
                "chapter": body.chapter,
                "topic": body.topic,
                "difficulty": body.difficulty,
                "question_specs": question_specs_str,
            },
            provider=body.provider,
            max_tokens=4096,
            context=f"Generate custom assessment for Class {body.grade} {body.subject}: {body.chapter}",
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

        return CustomAssessmentResponse(
            subject=body.subject,
            grade=body.grade,
            chapter=body.chapter,
            topic=body.topic,
            total_marks=total_marks,
            sections=sections,
            total_time_minutes=data.get("total_time_minutes", f"{total_marks} min"),
            instructions=data.get("instructions", []),
        )

    async def generate_exam_paper(self, body: ExamPaperGenerateRequest) -> ExamPaperGenerateResponse:
        """Generate a full exam paper following CBSE pattern."""
        _validate_grade(body.grade)
        if body.easy_pct + body.medium_pct + body.hard_pct != 100:
            raise ValueError("Difficulty percentages must sum to 100")

        logger.info(
            "Generating exam paper",
            extra={
                "grade": body.grade,
                "subject": body.subject,
                "chapters": body.chapters,
                "marks": body.total_marks,
            },
        )

        raw = await orchestrator.execute_with_retry(
            category="teacher_assistant",
            prompt_name="exam_paper",
            variables={
                "grade": str(body.grade),
                "subject": body.subject,
                "chapters": body.chapters,
                "total_marks": str(body.total_marks),
                "duration_minutes": str(body.duration_minutes),
                "easy_pct": str(body.easy_pct),
                "medium_pct": str(body.medium_pct),
                "hard_pct": str(body.hard_pct),
                "mcq_count": str(body.mcq_count),
                "vsa_count": str(body.vsa_count),
                "sa_count": str(body.sa_count),
                "la_count": str(body.la_count),
            },
            provider=body.provider,
            max_tokens=4096,
            context=f"Generate exam paper for Class {body.grade} {body.subject}: {body.chapters}",
            age_group=f"{body.grade * 2 - 1}-{body.grade * 2} years",
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
                        chapter=q.get("chapter", ""),
                        model_explanation=q.get("model_explanation"),
                    )
                )
            sections.append(
                ExamSection(
                    section_name=s.get("section_name", ""),
                    marks_per_question=s.get("marks_per_question", 1),
                    total_section_marks=s.get("total_section_marks", 0),
                    instructions=s.get("instructions", ""),
                    questions=questions,
                )
            )

        ak = data.get("answer_key")
        answer_key = None
        if ak:
            answer_key = AnswerKey(
                section_a_answers=ak.get("section_a_answers", []),
                section_b_key_points=ak.get("section_b_key_points", []),
                section_c_model_answers=ak.get("section_c_model_answers", []),
            )

        bp = data.get("blueprint")
        blueprint = None
        if bp:
            blueprint = ExamBlueprint(
                chapter_wise_marks=bp.get("chapter_wise_marks", {}),
                difficulty_breakdown=bp.get("difficulty_breakdown", {}),
                cognitive_breakdown=bp.get("cognitive_breakdown", {}),
            )

        return ExamPaperGenerateResponse(
            subject=body.subject,
            grade=body.grade,
            exam_title=data.get("exam_title", "Examination"),
            total_marks=body.total_marks,
            duration_minutes=body.duration_minutes,
            general_instructions=data.get("general_instructions", []),
            sections=sections,
            answer_key=answer_key,
            blueprint=blueprint,
        )


# Singleton instance
teacher_assistant_service = TeacherAssistantService()