"""Activity generation and CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from starlette import status

from app.db.session import get_session
from app.models.activity import Activity
from app.models.story import Story
from app.schemas.activity import ActivityGenerateRequest, ActivityGenerateResponse, ActivityRead
from app.services.analytics import EVENT_ACTIVITY_GENERATED, analytics
from app.services.education_engine import generate_activity as engine_generate_activity
from app.utils.logger import get_logger

logger = get_logger("app.api.activities")
router = APIRouter(prefix="/activities", tags=["activities"])


def _resolve_story_text(body, session):
    if body.story_id:
        story = session.get(Story, body.story_id)
        if not story:
            raise ValueError(f"Story not found: id={body.story_id}")
        return story.content
    if body.story_text:
        return body.story_text
    raise ValueError("Either story_id or story_text is required")


@router.post("/generate", response_model=ActivityGenerateResponse, status_code=status.HTTP_201_CREATED, summary="Generate activity from a story")
async def create_activity(body: ActivityGenerateRequest, session: Session = Depends(get_session)):
    try:
        story_text = _resolve_story_text(body, session)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    payload = {"story_text": story_text, "age_group": body.age_group, "activity_mode": body.activity_mode, "provider": body.provider}
    try:
        result = await engine_generate_activity(payload)
    except Exception as e:
        logger.error("Activity generation failed", extra={"error": str(e)})
        raise HTTPException(status_code=502, detail=f"Education engine error: {str(e)}")
    activity = Activity(story_id=body.story_id, title=result.get("title", ""), materials=result.get("materials", ""), instructions=result.get("instructions", ""), challenge_question=result.get("challenge_question", ""), age_group=body.age_group, activity_mode=body.activity_mode)
    session.add(activity)
    session.commit()
    session.refresh(activity)
    analytics.track(EVENT_ACTIVITY_GENERATED, properties={"activity_id": activity.id, "story_id": body.story_id, "age_group": body.age_group, "activity_mode": body.activity_mode, "provider": result.get("provider", "unknown"), "model": result.get("model", "unknown")})
    return activity


@router.get("/{activity_id}", response_model=ActivityRead, summary="Get activity by ID")
async def get_activity(activity_id: int, session: Session = Depends(get_session)):
    activity = session.get(Activity, activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    return activity


@router.get("", response_model=list[ActivityRead], summary="List all activities")
async def list_activities(session: Session = Depends(get_session)):
    return session.exec(select(Activity).order_by(Activity.created_at.desc())).all()
