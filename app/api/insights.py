"""Insight endpoints — derived child understanding."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from starlette import status

from app.db.session import get_session
from app.models.child import Child
from app.schemas.insight import InsightGenerateRequest, InsightRead
from app.services.insights import generate_insights, get_insights_by_child

router = APIRouter(prefix="/children/{child_id}/insights", tags=["insights"])


@router.get(
    "",
    response_model=list[InsightRead],
    summary="List insights for a child",
    description="Retrieve active insights for a child, newest first.",
    responses={404: {"description": "Child not found"}},
)
async def list_insights_endpoint(
    child_id: int,
    session: Session = Depends(get_session),
):
    """List insights for a child."""
    child = session.get(Child, child_id)
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    return get_insights_by_child(child_id, session=session)


@router.post(
    "/generate",
    response_model=list[InsightRead],
    status_code=status.HTTP_201_CREATED,
    summary="Generate insights for a child",
    description="Process unprocessed signals and generate new insights for a child.",
    responses={
        404: {"description": "Child not found"},
    },
)
async def generate_insights_endpoint(
    child_id: int,
    body: InsightGenerateRequest,
    session: Session = Depends(get_session),
):
    """Trigger insight generation from unprocessed signals."""
    child = session.get(Child, child_id)
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    since = body.since if body.since else datetime.min
    return generate_insights(child_id, since=since, session=session)
