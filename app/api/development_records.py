"""Development record endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from starlette import status

from app.db.session import get_session
from app.models.child import Child
from app.schemas.development_record import DevelopmentRecordRead, DevelopmentRecordUpdate
from app.services.development_records import get_or_create_record, get_record, update_record

router = APIRouter(prefix="/development-records", tags=["development-records"])


@router.get(
    "/{child_id}",
    response_model=DevelopmentRecordRead,
    summary="Get child development record",
    description="Retrieve the current developmental understanding snapshot for a child. Creates one if missing.",
    responses={404: {"description": "Child not found"}},
)
async def get_development_record(child_id: int, session: Session = Depends(get_session)):
    """Get the development record for a child."""
    child = session.get(Child, child_id)
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    record = get_or_create_record(child_id, session)
    return record


@router.put(
    "/{child_id}",
    response_model=DevelopmentRecordRead,
    summary="Update child development record",
    description="Update a child's development record (partial update).",
    responses={404: {"description": "Child not found"}},
)
async def update_development_record(
    child_id: int,
    body: DevelopmentRecordUpdate,
    session: Session = Depends(get_session),
):
    """Update a child's development record."""
    child = session.get(Child, child_id)
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    record = update_record(child_id, body, session)
    if not record:
        raise HTTPException(status_code=404, detail="Development record not found")
    return record
