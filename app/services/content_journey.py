"""Content Journey service — track what content was shown to children."""

from datetime import datetime
from typing import Any

from sqlmodel import Session, select

from app.models.content_journey import ContentJourney


def create_journal_entry(
    child_id: int,
    content_type: str,
    content_id: int,
    source: str,
    content_metadata: dict[str, Any] | None = None,
    session: Session = None,
) -> ContentJourney:
    """Log a content exposure for a child."""
    entry = ContentJourney(
        child_id=child_id,
        content_type=content_type,
        content_id=content_id,
        source=source,
        content_metadata=content_metadata,
    )
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry


def get_journey_by_child(
    child_id: int, limit: int = 50, session: Session = None
) -> list[ContentJourney]:
    """Get recent content journey entries for a child."""
    statement = (
        select(ContentJourney)
        .where(ContentJourney.child_id == child_id)
        .order_by(ContentJourney.created_at.desc())
        .limit(limit)
    )
    return list(session.exec(statement).all())


def get_journey_by_content_type(
    child_id: int, content_type: str, session: Session = None
) -> list[ContentJourney]:
    """Get journey entries filtered by content type."""
    statement = (
        select(ContentJourney)
        .where(
            ContentJourney.child_id == child_id,
            ContentJourney.content_type == content_type,
        )
        .order_by(ContentJourney.created_at.desc())
    )
    return list(session.exec(statement).all())
