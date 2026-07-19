"""Parent profile service — CRUD operations for parent profiles."""

from datetime import datetime

from sqlmodel import Session, select

from app.models.parent import Parent
from app.schemas.parent import ParentCreate, ParentUpdate


def create_parent(body: ParentCreate, session: Session) -> Parent:
    """Create a new parent profile and persist it to the database.

    Args:
        body: Parent creation request with profile details.
        session: Database session.

    Returns:
        The saved `Parent` row (with `id` and timestamps populated).

    Raises:
        ValueError: If a parent with the same email or mobile number already exists.
    """
    # Check for duplicates on email / mobile (only if provided)
    if body.email:
        existing = session.exec(
            select(Parent).where(Parent.email == body.email)
        ).first()
        if existing:
            raise ValueError(f"A parent with email '{body.email}' already exists")
    if body.mobile_number:
        existing = session.exec(
            select(Parent).where(Parent.mobile_number == body.mobile_number)
        ).first()
        if existing:
            raise ValueError(
                f"A parent with mobile number '{body.mobile_number}' already exists"
            )

    parent = Parent(
        name=body.name,
        email=body.email,
        mobile_number=body.mobile_number,
        preferred_language=body.preferred_language,
        avatar_url=body.avatar_url,
    )
    session.add(parent)
    session.commit()
    session.refresh(parent)
    return parent


def get_parent(parent_id: int, session: Session) -> Parent | None:
    """Get a single parent by ID.

    Args:
        parent_id: The parent's unique identifier.
        session: Database session.

    Returns:
        The `Parent` row, or `None` if not found.
    """
    return session.get(Parent, parent_id)


def get_parent_profile(parent_id: int, session: Session) -> Parent | None:
    """Get the current parent's profile.

    Convenience alias for `get_parent` — used by the /parents/profile endpoint.

    Args:
        parent_id: The parent's unique identifier.
        session: Database session.

    Returns:
        The `Parent` row, or `None` if not found.
    """
    return get_parent(parent_id, session)


def update_parent(parent_id: int, body: ParentUpdate, session: Session) -> Parent | None:
    """Update an existing parent profile.

    Only the fields provided in the request body are updated (partial update).

    Args:
        parent_id: The parent's unique identifier.
        body: Parent update request with optional fields.
        session: Database session.

    Returns:
        The updated `Parent` row, or `None` if not found.

    Raises:
        ValueError: If updating email/mobile would collide with another parent.
    """
    parent = session.get(Parent, parent_id)
    if not parent:
        return None

    update_data = body.model_dump(exclude_unset=True, by_alias=False)

    # Uniqueness checks for email / mobile if they're being changed
    if "email" in update_data and update_data["email"]:
        existing = session.exec(
            select(Parent).where(
                Parent.email == update_data["email"],
                Parent.id != parent_id,
            )
        ).first()
        if existing:
            raise ValueError(f"Email '{update_data['email']}' is already in use")
    if "mobile_number" in update_data and update_data["mobile_number"]:
        existing = session.exec(
            select(Parent).where(
                Parent.mobile_number == update_data["mobile_number"],
                Parent.id != parent_id,
            )
        ).first()
        if existing:
            raise ValueError(
                f"Mobile number '{update_data['mobile_number']}' is already in use"
            )

    for field, value in update_data.items():
        setattr(parent, field, value)

    parent.updated_at = datetime.utcnow()
    session.add(parent)
    session.commit()
    session.refresh(parent)
    return parent