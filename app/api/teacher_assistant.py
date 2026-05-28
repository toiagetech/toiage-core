"""Teacher Assistant API endpoints — generate educational assessments."""

from fastapi import APIRouter, HTTPException
from starlette import status

from app.schemas.assessment import (
    MCQGenerateRequest,
    MCQGenerateResponse,
    ShortAnswerGenerateRequest,
    ShortAnswerGenerateResponse,
    LongAnswerGenerateRequest,
    LongAnswerGenerateResponse,
    CustomAssessmentGenerateRequest,
    CustomAssessmentResponse,
    ExamPaperGenerateRequest,
    ExamPaperGenerateResponse,
)
from app.schemas.worksheet import (
    WorksheetGenerateRequest,
    WorksheetGenerateResponse,
)
from app.services.teacher_assistant import teacher_assistant_service

router = APIRouter(prefix="/api/v1/teacher-assistant", tags=["teacher-assistant"])


@router.post(
    "/mcq",
    response_model=MCQGenerateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate multiple-choice questions",
    description="Generate CBSE-aligned multiple-choice questions for a given chapter and topic.",
    responses={400: {"description": "Invalid request"}},
)
async def generate_mcq(body: MCQGenerateRequest):
    """Generate multiple-choice questions for a chapter/topic."""
    try:
        return await teacher_assistant_service.generate_mcq(body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/custom-assessment",
    response_model=CustomAssessmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a custom assessment",
    description=(
        "Generate a custom assessment where the teacher specifies question types, counts, and marks. "
        "Example: 5 MCQs (1 mark each) + 3 short answers (2 marks each) + 2 long answers (5 marks each)."
    ),
    responses={400: {"description": "Invalid request"}},
)
async def generate_custom_assessment(body: CustomAssessmentGenerateRequest):
    """Generate a custom assessment with teacher-specified question types."""
    try:
        return await teacher_assistant_service.generate_custom_assessment(body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/short-answer",
    response_model=ShortAnswerGenerateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate short-answer questions",
    description="Generate CBSE-aligned short-answer questions (2-3 marks each) for a given chapter.",
    responses={400: {"description": "Invalid request"}},
)
async def generate_short_answer(body: ShortAnswerGenerateRequest):
    """Generate short-answer questions for a chapter/topic."""
    try:
        return await teacher_assistant_service.generate_short_answer(body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/long-answer",
    response_model=LongAnswerGenerateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate long-answer questions",
    description="Generate CBSE-aligned long-answer questions (5 marks each) for a given chapter.",
    responses={400: {"description": "Invalid request"}},
)
async def generate_long_answer(body: LongAnswerGenerateRequest):
    """Generate long-answer questions for a chapter/topic."""
    try:
        return await teacher_assistant_service.generate_long_answer(body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/worksheet",
    response_model=WorksheetGenerateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a practice worksheet",
    description="Generate a CBSE-aligned practice worksheet with mixed question types for a given chapter.",
    responses={400: {"description": "Invalid request"}},
)
async def generate_worksheet(body: WorksheetGenerateRequest):
    """Generate a practice worksheet for a chapter/topic."""
    try:
        return await teacher_assistant_service.generate_worksheet(body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/exam-paper",
    response_model=ExamPaperGenerateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a full exam paper",
    description=(
        "Generate a complete CBSE exam paper with specified marks distribution, "
        "difficulty balance, and answer key. Supports periodic tests, half-yearly, and annual exam patterns."
    ),
    responses={400: {"description": "Invalid request (difficulty percentages must sum to 100)"}},
)
async def generate_exam_paper(body: ExamPaperGenerateRequest):
    """Generate a full exam paper following CBSE pattern."""
    try:
        return await teacher_assistant_service.generate_exam_paper(body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))