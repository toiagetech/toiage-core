"""Signal endpoints — raw observation ingestion."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from starlette import status

from app.db.session import get_session
from app.models.child import Child
from app.schemas.signal import SignalBulkCreate, SignalCreate, SignalRead
from app.services.signals import bulk_create_signals, create_signal, get_signals_by_child

router = APIRouter(prefix="/children/{child_id}/signals", tags=["signals"])


@router.post(
    "",
    response_model=SignalRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a signal for a child",
    description="Record a single raw observation signal for a child.",
    responses={
        404: {"description": "Child not found"},
        422: {"description": "Validation error"},
    },
)
async def create_signal_endpoint(
    child_id: int,
    body: SignalCreate,
    session: Session = Depends(get_session),
):
    """Create a single signal."""
    child = session.get(Child, child_id)
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    # Override child_id from path
    body.child_id = child_id
    return create_signal(body, session)


@router.post(
    "/bulk",
    response_model=list[SignalRead],
    status_code=status.HTTP_201_CREATED,
    summary="Bulk create signals for a child",
    description="Record multiple raw observation signals in one call.",
    responses={
        404: {"description": "Child not found"},
        422: {"description": "Validation error"},
    },
)
async def bulk_create_signals_endpoint(
    child_id: int,
    body: SignalBulkCreate,
    session: Session = Depends(get_session),
):
    """Bulk create signals."""
    child = session.get(Child, child_id)
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    body.child_id = child_id
    return bulk_create_signals(body, session)


@router.get(
    "",
    response_model=list[SignalRead],
    summary="List signals for a child",
    description="Retrieve recent signals for a child, newest first.",
    responses={404: {"description": "Child not found"}},
)
async def list_signals_endpoint(
    child_id: int,
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_session),
):
    """List signals for a child."""
    child = session.get(Child, child_id)
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    return get_signals_by_child(child_id, limit=limit, session=session)
