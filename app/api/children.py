"""Child profile CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from starlette import status

from app.db.session import get_session
from app.schemas.child import ChildCreate, ChildRead, ChildUpdate
from app.services.children import (
    create_child,
    delete_child,
    get_child,
    get_children_by_parent,
    update_child,
)

router = APIRouter(prefix="/children", tags=["children"])


@router.post(
    "",
    response_model=ChildRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new child profile",
    description=(
        "Create a new child profile for the authenticated parent. "
        "The profile is stored in the database and used by the story/activity "
        "generation pipeline to personalize content."
    ),
    responses={
        422: {"description": "Validation error (missing required fields)"},
    },
)
async def create_child_endpoint(
    body: ChildCreate,
    session: Session = Depends(get_session),
):
    """Create and save a new child profile."""
    child = create_child(body, session)
    return child


@router.get(
    "",
    response_model=list[ChildRead],
    summary="Get all children for the current parent",
    description=(
        "Retrieve all child profiles belonging to a parent, ordered by "
        "creation date (newest first). Provide the parent's user ID via the "
        "`parentId` query parameter."
    ),
    responses={
        422: {"description": "Missing parentId query parameter"},
    },
)
async def list_children_endpoint(
    parent_id: str = Query(..., alias="parentId", description="The parent's user ID"),
    session: Session = Depends(get_session),
):
    """List all children for a parent."""
    children = get_children_by_parent(parent_id, session)
    return children


@router.get(
    "/{child_id}",
    response_model=ChildRead,
    summary="Get a specific child's details",
    description="Retrieve a single child profile by its unique identifier.",
    responses={
        404: {"description": "Child not found"},
    },
)
async def get_child_endpoint(
    child_id: int,
    session: Session = Depends(get_session),
):
    """Retrieve a single child by ID."""
    child = get_child(child_id, session)
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")
    return child


@router.put(
    "/{child_id}",
    response_model=ChildRead,
    summary="Update a child by ID",
    description=(
        "Update an existing child profile. Only the fields provided in the "
        "request body are updated (partial update)."
    ),
    responses={
        404: {"description": "Child not found"},
        422: {"description": "Validation error"},
    },
)
async def update_child_endpoint(
    child_id: int,
    body: ChildUpdate,
    session: Session = Depends(get_session),
):
    """Update a child profile by ID."""
    child = update_child(child_id, body, session)
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")
    return child


@router.delete(
    "/{child_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a child by ID",
    description="Delete a child profile by its unique identifier.",
    responses={
        404: {"description": "Child not found"},
    },
)
async def delete_child_endpoint(
    child_id: int,
    session: Session = Depends(get_session),
):
    """Delete a child profile by ID."""
    deleted = delete_child(child_id, session)
    if not deleted:
        raise HTTPException(status_code=404, detail="Child not found")
    return None