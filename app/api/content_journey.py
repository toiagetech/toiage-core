"""Content Journey endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from starlette import status

from app.db.session import get_session
from app.models.child import Child
from app.schemas.content_journey import ContentJourneyRead
from app.services.content_journey import (
    get_journey_by_child,
    get_journey_by_content_type,
)

router = APIRouter(prefix="/children/{child_id}/journey", tags=["content-journey"])


@router.get(
    "",
    response_model=list[ContentJourneyRead],
    summary="Get content journey for a child",
    description="Retrieve the content journey log for a child.",
    responses={404: {"description": "Child not found"}},
)
async def get_journey_endpoint(
    child_id: int,
    content_type: str | None = Query(default=None, description="Filter by content type"),
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_session),
):
    """Get content journey for a child."""
    child = session.get(Child, child_id)
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    if content_type:
        return get_journey_by_content_type(child_id, content_type, session=session)
    return get_journey_by_child(child_id, limit=limit, session=session)
