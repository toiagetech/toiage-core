"""Parent profile endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from starlette import status

from app.db.session import get_session
from app.schemas.parent import ParentCreate, ParentRead, ParentUpdate
from app.services.parents import (
    create_parent,
    get_parent_profile,
    update_parent,
)

router = APIRouter(prefix="/parents", tags=["parents"])


@router.post(
    "",
    response_model=ParentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a parent profile after registration",
    description=(
        "Create a new parent profile. The parent is the main app user who "
        "registers via mobile number or email. At least one of `email` or "
        "`mobileNumber` must be provided."
    ),
    responses={
        400: {"description": "A parent with the same email/mobile already exists"},
        422: {"description": "Validation error (missing required fields)"},
    },
)
async def create_parent_endpoint(
    body: ParentCreate,
    session: Session = Depends(get_session),
):
    """Create and save a new parent profile."""
    try:
        parent = create_parent(body, session)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return parent


@router.get(
    "/profile",
    response_model=ParentRead,
    summary="Get the current parent's profile",
    description=(
        "Retrieve the current parent's profile. Provide the parent's ID via "
        "the `parentId` query parameter."
    ),
    responses={
        404: {"description": "Parent not found"},
        422: {"description": "Missing parentId query parameter"},
    },
)
async def get_parent_profile_endpoint(
    parent_id: int = Query(..., alias="parentId", description="The parent's user ID"),
    session: Session = Depends(get_session),
):
    """Retrieve the current parent's profile."""
    parent = get_parent_profile(parent_id, session)
    if not parent:
        raise HTTPException(status_code=404, detail="Parent not found")
    return parent


@router.put(
    "/profile",
    response_model=ParentRead,
    summary="Update the current parent's profile",
    description=(
        "Update the current parent's profile. Only the fields provided in the "
        "request body are updated (partial update). Provide the parent's ID "
        "via the `parentId` query parameter."
    ),
    responses={
        404: {"description": "Parent not found"},
        400: {"description": "Email/mobile already in use by another parent"},
        422: {"description": "Validation error"},
    },
)
async def update_parent_profile_endpoint(
    body: ParentUpdate,
    parent_id: int = Query(..., alias="parentId", description="The parent's user ID"),
    session: Session = Depends(get_session),
):
    """Update the current parent's profile."""
    try:
        parent = update_parent(parent_id, body, session)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if not parent:
        raise HTTPException(status_code=404, detail="Parent not found")
    return parent