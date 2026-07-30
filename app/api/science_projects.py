"""Science Project generation API endpoint."""

import json
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from starlette import status

from app.db.session import get_session
from app.models.project_record import ScienceProjectRecord
from app.schemas.science_project import ScienceProjectGenerateRequest, ScienceProjectGenerateResponse, ScienceProjectResponse
from app.services.education_engine import generate_science_project as engine_generate_science_project
from app.utils.logger import get_logger

logger = get_logger("app.api.science_projects")
router = APIRouter(prefix="/api/v1/science-projects", tags=["science-projects"])


@router.post("/generate", response_model=ScienceProjectGenerateResponse, status_code=status.HTTP_201_CREATED, summary="Generate a science project")
async def generate_science_project(body: ScienceProjectGenerateRequest, session: Session = Depends(get_session)):
    payload = {"grade": body.grade, "subject": body.subject, "topic": body.topic, "difficulty": body.difficulty, "budget": body.budget, "provider": body.provider}
    try:
        result = await engine_generate_science_project(payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Science project generation failed", extra={"error": str(e)})
        raise HTTPException(status_code=502, detail=f"Education engine error: {str(e)}")
    project = ScienceProjectResponse(**result)
    record = ScienceProjectRecord(project_title=project.project_title, subject=project.subject, grade=project.grade, topic=project.topic, difficulty=project.difficulty, budget=body.budget, provider=body.provider, short_description=project.short_description, curriculum_alignment=project.curriculum_alignment, estimated_build_time=project.estimated_build_time, estimated_cost=project.estimated_cost, overall_difficulty=project.overall_difficulty, scientific_principle=project.scientific_principle, simple_explanation=project.simple_explanation, adult_supervision_required=project.adult_supervision_required, response_json=json.dumps(project.model_dump(), default=str))
    session.add(record)
    session.commit()
    session.refresh(record)
    return ScienceProjectGenerateResponse(project=project, project_id=record.id, created_at=record.created_at, prompt_tokens_used=0, completion_tokens_used=0)


@router.get("", response_model=list[ScienceProjectGenerateResponse], summary="List all science projects")
async def list_science_projects(session: Session = Depends(get_session)):
    records = session.exec(select(ScienceProjectRecord).order_by(ScienceProjectRecord.created_at.desc())).all()
    results = []
    for record in records:
        try:
            project_data = json.loads(record.response_json) if record.response_json else {}
            project = ScienceProjectResponse(**project_data)
        except Exception:
            project = ScienceProjectResponse(project_title=record.project_title, subject=record.subject, grade=record.grade, topic=record.topic, difficulty=record.difficulty, overall_difficulty=record.overall_difficulty, short_description=record.short_description, curriculum_alignment=record.curriculum_alignment, estimated_build_time=record.estimated_build_time, estimated_cost=record.estimated_cost, scientific_principle=record.scientific_principle, simple_explanation=record.simple_explanation, adult_supervision_required=record.adult_supervision_required, provider=record.provider)
        results.append(ScienceProjectGenerateResponse(project=project, project_id=record.id, created_at=record.created_at))
    return results


@router.get("/{project_id}", response_model=ScienceProjectGenerateResponse, summary="Get science project by ID")
async def get_science_project(project_id: int, session: Session = Depends(get_session)):
    record = session.get(ScienceProjectRecord, project_id)
    if not record:
        raise HTTPException(status_code=404, detail="Science project not found")
    try:
        project_data = json.loads(record.response_json) if record.response_json else {}
        project = ScienceProjectResponse(**project_data)
    except Exception:
        project = ScienceProjectResponse(project_title=record.project_title, subject=record.subject, grade=record.grade, topic=record.topic, difficulty=record.difficulty, overall_difficulty=record.overall_difficulty, short_description=record.short_description, curriculum_alignment=record.curriculum_alignment, estimated_build_time=record.estimated_build_time, estimated_cost=record.estimated_cost, scientific_principle=record.scientific_principle, simple_explanation=record.simple_explanation, adult_supervision_required=record.adult_supervision_required, provider=record.provider)
    return ScienceProjectGenerateResponse(project=project, project_id=record.id, created_at=record.created_at)
