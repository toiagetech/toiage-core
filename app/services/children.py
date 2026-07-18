"""Child profile service — CRUD operations for child profiles."""

from datetime import datetime

from sqlmodel import Session, select

from app.models.child import Child
from app.schemas.child import ChildCreate, ChildUpdate


def create_child(body: ChildCreate, session: Session) -> Child:
    """Create a new child profile and persist it to the database.

    Args:
        body: Child creation request with profile details.
        session: Database session.

    Returns:
        The saved `Child` row (with `id` and timestamps populated).
    """
    child = Child(
        parent_id=body.parent_id,
        name=body.name,
        nick_name=body.nick_name,
        date_of_birth=body.date_of_birth,
        gender=body.gender,
        preferred_language=body.preferred_language,
        school_name=body.school_name,
        current_class=body.current_class,
        board=body.board,
        interests=body.interests,
        favourite_subjects=body.favourite_subjects,
        learning_style=body.learning_style,
        existing_toys=body.existing_toys,
        household_materials=body.household_materials,
        special_notes=body.special_notes,
    )
    session.add(child)
    session.commit()
    session.refresh(child)
    return child


def get_children_by_parent(parent_id: str, session: Session) -> list[Child]:
    """Get all children belonging to a parent.

    Args:
        parent_id: The parent's user ID.
        session: Database session.

    Returns:
        List of `Child` rows ordered by creation date (newest first).
    """
    statement = (
        select(Child)
        .where(Child.parent_id == parent_id)
        .order_by(Child.created_at.desc())
    )
    return list(session.exec(statement).all())


def get_child(child_id: int, session: Session) -> Child | None:
    """Get a single child by ID.

    Args:
        child_id: The child's unique identifier.
        session: Database session.

    Returns:
        The `Child` row, or `None` if not found.
    """
    return session.get(Child, child_id)


def update_child(child_id: int, body: ChildUpdate, session: Session) -> Child | None:
    """Update an existing child profile.

    Only the fields provided in the request body are updated (partial update).

    Args:
        child_id: The child's unique identifier.
        body: Child update request with optional fields.
        session: Database session.

    Returns:
        The updated `Child` row, or `None` if not found.
    """
    child = session.get(Child, child_id)
    if not child:
        return None

    # Apply only the fields that were provided (exclude unset)
    update_data = body.model_dump(exclude_unset=True, by_alias=False)
    for field, value in update_data.items():
        setattr(child, field, value)

    child.updated_at = datetime.utcnow()
    session.add(child)
    session.commit()
    session.refresh(child)
    return child


def delete_child(child_id: int, session: Session) -> bool:
    """Delete a child profile by ID.

    Args:
        child_id: The child's unique identifier.
        session: Database session.

    Returns:
        `True` if the child was deleted, `False` if not found.
    """
    child = session.get(Child, child_id)
    if not child:
        return False

    session.delete(child)
    session.commit()
    return True