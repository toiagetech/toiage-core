from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db.session import get_session
from app.models.activity import Activity
from app.schemas.activity import (
    ActivityGenerateRequest,
    ActivityGenerateResponse,
    ActivityRead,
)
from app.services.activities import generate_activity

router = APIRouter(prefix="/activities", tags=["activities"])


@router.post("/generate", response_model=ActivityGenerateResponse, status_code=201)
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


@router.get("/{activity_id}", response_model=ActivityRead)
async def get_activity(
    activity_id: int,
    session: Session = Depends(get_session),
):
    """Retrieve a single activity by ID."""
    activity = session.get(Activity, activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    return activity


@router.get("", response_model=list[ActivityRead])
async def list_activities(session: Session = Depends(get_session)):
    """List all activities."""
    activities = session.exec(
        select(Activity).order_by(Activity.created_at.desc())
    ).all()
    return activities