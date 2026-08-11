"""Development record service — CRUD and confidence scoring."""

from datetime import datetime

from sqlmodel import Session, select

from app.models.development_record import ChildDevelopmentRecord
from app.schemas.development_record import DevelopmentRecordUpdate


def get_or_create_record(child_id: int, session: Session) -> ChildDevelopmentRecord:
    """Get the development record for a child, creating one if missing."""
    statement = select(ChildDevelopmentRecord).where(
        ChildDevelopmentRecord.child_id == child_id
    )
    record = session.exec(statement).first()
    if not record:
        record = ChildDevelopmentRecord(child_id=child_id)
        session.add(record)
        session.commit()
        session.refresh(record)
    return record


def get_record(child_id: int, session: Session) -> ChildDevelopmentRecord | None:
    """Get the development record for a child."""
    statement = select(ChildDevelopmentRecord).where(
        ChildDevelopmentRecord.child_id == child_id
    )
    return session.exec(statement).first()


def update_record(
    child_id: int, body: DevelopmentRecordUpdate, session: Session
) -> ChildDevelopmentRecord | None:
    """Update a child's development record."""
    record = get_record(child_id, session)
    if not record:
        return None

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(record, field):
            setattr(record, field, value)

    record.updated_at = datetime.utcnow()
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def increment_confidence(child_id: int, delta: float, session: Session) -> float:
    """Increase the understanding confidence for a child.

    Confidence is capped at 1.0.
    """
    record = get_or_create_record(child_id, session)
    record.understanding_confidence = min(1.0, record.understanding_confidence + delta)
    record.updated_at = datetime.utcnow()
    session.add(record)
    session.commit()
    session.refresh(record)
    return record.understanding_confidence


def mark_signal_processed(child_id: int, session: Session) -> None:
    """Update the development record after a signal is processed."""
    record = get_or_create_record(child_id, session)
    record.total_signals_processed += 1
    record.last_signal_at = datetime.utcnow()
    record.updated_at = datetime.utcnow()
    session.add(record)
