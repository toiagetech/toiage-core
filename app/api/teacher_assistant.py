"""Teacher Assistant API endpoints — generate educational assessments.

This is the business orchestration layer. It:
1. Saves/finds the assessment pattern
2. Calls the education engine via HTTP to generate the assessment
3. Saves the generation history
4. Returns the response

It never calls LLM providers directly.
"""

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from starlette import status

from app.db.session import get_session
from app.models.assessment_pattern import AssessmentConfig
from app.models.generation_history import AssessmentGenerationHistory
from app.schemas.assessment import (
    GenerateAssessmentRequest,
    GenerateAssessmentResponse,
)
from app.services.education_engine import generate_assessment as engine_generate_assessment
from app.utils.logger import get_logger

logger = get_logger("app.api.teacher_assistant")

router = APIRouter(prefix="/api/v1/teacher-assistant", tags=["teacher-assistant"])


@router.post(
    "/generate",
    response_model=GenerateAssessmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate assessment with teacher-specified pattern",
    description=(
        "Generate a CBSE-aligned assessment where the teacher specifies question types, counts, and marks per question. "
        "The pattern is auto-saved for reuse. Supports any question types: mcq, short_answer, long_answer, fill_blanks, true_false, match, etc."
    ),
    responses={
        400: {"description": "Invalid request"},
        502: {"description": "Education engine unavailable"},
    },
)
async def generate_assessment(
    body: GenerateAssessmentRequest,
    session: Session = Depends(get_session),
):
    """Generate an assessment with teacher-specified question types and auto-save the pattern."""
    try:
        total_marks = sum(spec.count * spec.marks_per_question for spec in body.question_specs)

        # --- Step 1: Save or find existing pattern ---
        pattern_name = body.pattern_name or f"Class {body.grade} {body.subject} - {body.topic or body.chapter}"

        existing = session.exec(
            select(AssessmentConfig).where(
                AssessmentConfig.grade == body.grade,
                AssessmentConfig.subject == body.subject,
                AssessmentConfig.pattern_name == pattern_name,
            )
        ).first()

        if existing:
            pattern_id = existing.id
        else:
            pattern = AssessmentConfig(
                grade=body.grade,
                subject=body.subject,
                pattern_name=pattern_name,
                total_marks=total_marks,
                duration_minutes=body.duration_minutes or 180,
                mcq_count=0,
                vsa_count=0,
                sa_count=0,
                la_count=0,
                easy_pct=30,
                medium_pct=50,
                hard_pct=20,
                marks_distribution=json.dumps([s.model_dump() for s in body.question_specs]),
            )
            session.add(pattern)
            session.commit()
            session.refresh(pattern)
            pattern_id = pattern.id

        # --- Step 2: Build payload and call the education engine ---
        payload = {
            "grade": body.grade,
            "subject": body.subject,
            "chapter": body.chapter,
            "topic": body.topic,
            "difficulty": body.difficulty,
            "question_specs": [s.model_dump() for s in body.question_specs],
            "provider": body.provider,
        }

        try:
            result = await engine_generate_assessment(payload)
        except Exception as e:
            logger.error("Assessment generation failed — education engine error", extra={"error": str(e)})
            raise HTTPException(status_code=502, detail=f"Education engine error: {str(e)}")

        # --- Step 3: Save generation history ---
        history = AssessmentGenerationHistory(
            pattern_id=pattern_id,
            grade=body.grade,
            subject=body.subject,
            chapter=body.chapter,
            topic=body.topic,
            question_specs=json.dumps([s.model_dump() for s in body.question_specs]),
            generated_output=json.dumps(result.get("sections", []), default=str),
            total_marks=total_marks,
            provider=body.provider,
        )
        session.add(history)
        session.commit()
        session.refresh(history)

        # --- Step 4: Return response with IDs ---
        return GenerateAssessmentResponse(
            subject=result.get("subject", body.subject),
            grade=result.get("grade", body.grade),
            chapter=result.get("chapter", body.chapter),
            topic=result.get("topic", body.topic),
            total_marks=total_marks,
            sections=result.get("sections", []),
            total_time_minutes=result.get("total_time_minutes", ""),
            instructions=result.get("instructions", []),
            id=history.id,
            pattern_id=pattern_id,
            pattern_name=pattern_name,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/history",
    response_model=list[dict],
    summary="List generation history",
    description="Retrieve all past assessment generations ordered by creation date (newest first).",
)
async def list_generation_history(session: Session = Depends(get_session)):
    """List all assessment generation history."""
    records = session.exec(
        select(AssessmentGenerationHistory).order_by(AssessmentGenerationHistory.created_at.desc()).limit(50)
    ).all()
    return [
        {
            "id": r.id,
            "pattern_id": r.pattern_id,
            "grade": r.grade,
            "subject": r.subject,
            "chapter": r.chapter,
            "topic": r.topic,
            "total_marks": r.total_marks,
            "provider": r.provider,
            "created_at": r.created_at.isoformat(),
        }
        for r in records
    ]


@router.get(
    "/history/{history_id}",
    response_model=GenerateAssessmentResponse,
    summary="Get generation by ID",
    description="Retrieve a specific generation with full section details.",
    responses={404: {"description": "Generation not found"}},
)
async def get_generation(history_id: int, session: Session = Depends(get_session)):
    """Retrieve a specific generation by ID."""
    record = session.get(AssessmentGenerationHistory, history_id)
    if not record:
        raise HTTPException(status_code=404, detail="Generation not found")

    try:
        sections = json.loads(record.generated_output) if record.generated_output else []
    except (json.JSONDecodeError, Exception):
        sections = []

    return GenerateAssessmentResponse(
        subject=record.subject,
        grade=record.grade,
        chapter=record.chapter,
        topic=record.topic,
        total_marks=record.total_marks,
        sections=sections,
        total_time_minutes="",
        instructions=[],
        id=record.id,
        pattern_id=record.pattern_id,
    )