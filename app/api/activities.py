"""Activity generation and CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from starlette import status

from app.db.session import get_session
from app.models.activity import Activity
from app.schemas.activity import (
    ActivityGenerateRequest,
    ActivityGenerateResponse,
    ActivityRead,
)
from app.services.activities import generate_activity

router = APIRouter(prefix="/activities", tags=["activities"])


@router.post(
    "/generate",
    response_model=ActivityGenerateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate activity from a story",
    description=(
        "Generate a hands-on, educational activity based on a story. "
        "Provide either an existing story_id or raw story_text. "
        "The activity includes a title, materials list, step-by-step instructions, and an open-ended challenge question. "
        "Supports 'household' mode (common items) and 'toy-kit' mode (toys/crafts)."
    ),
    responses={
        400: {"description": "Invalid request (missing story_id and story_text, or story not found)"},
    },
)
async def create_activity(
    body: ActivityGenerateRequest,
    session: Session = Depends(get_session),
):
    """Generate a hands-on activity from a story and save it."""
    try:
        activity = await generate_activity(body, session)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return activity


@router.get(
    "/{activity_id}",
    response_model=ActivityRead,
    summary="Get activity by ID",
    description="Retrieve a single generated activity by its unique identifier.",
    responses={
        404: {"description": "Activity not found"},
    },
)
async def get_activity(
    activity_id: int,
    session: Session = Depends(get_session),
):
    """Retrieve a single activity by ID."""
    activity = session.get(Activity, activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    return activity


@router.get(
    "",
    response_model=list[ActivityRead],
    summary="List all activities",
    description="Retrieve all generated activities ordered by creation date (newest first).",
)
async def list_activities(session: Session = Depends(get_session)):
    """List all activities."""
    activities = session.exec(
        select(Activity).order_by(Activity.created_at.desc())
    ).all()
    return activities