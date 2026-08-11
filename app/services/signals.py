"""Signal service — ingestion, processing, and retrieval."""

from datetime import datetime
from typing import Any

from sqlmodel import Session, select

from app.models.development_record import ChildDevelopmentRecord
from app.models.signal import Signal
from app.schemas.signal import SignalBulkCreate, SignalCreate


def create_signal(body: SignalCreate, session: Session) -> Signal:
    """Create a single signal for a child."""
    signal = Signal(
        child_id=body.child_id,
        signal_type=body.signal_type,
        source=body.source,
        category=body.category,
        data=body.data,
        confidence=body.confidence,
        recorded_at=body.recorded_at,
    )
    session.add(signal)
    session.commit()
    session.refresh(signal)
    return signal


def bulk_create_signals(body: SignalBulkCreate, session: Session) -> list[Signal]:
    """Create multiple signals for a child in one transaction."""
    signals = []
    for item in body.signals:
        signal = Signal(
            child_id=body.child_id,
            signal_type=item.signal_type,
            source=body.source,
            category=item.category,
            data=item.data,
            confidence=item.confidence,
            recorded_at=item.recorded_at,
        )
        session.add(signal)
        signals.append(signal)

    session.commit()
    for signal in signals:
        session.refresh(signal)
    return signals


def get_signals_by_child(
    child_id: int, limit: int = 100, session: Session = None
) -> list[Signal]:
    """Get recent signals for a child, newest first."""
    statement = (
        select(Signal)
        .where(Signal.child_id == child_id)
        .order_by(Signal.created_at.desc())
        .limit(limit)
    )
    return list(session.exec(statement).all())


def get_unprocessed_signals(session: Session, limit: int = 100) -> list[Signal]:
    """Get unprocessed signals across all children."""
    statement = (
        select(Signal)
        .where(Signal.processed == False)  # noqa: E712
        .order_by(Signal.created_at.asc())
        .limit(limit)
    )
    return list(session.exec(statement).all())


def mark_processed(signal_ids: list[int], session: Session) -> None:
    """Mark signals as processed after insight generation."""
    for sid in signal_ids:
        signal = session.get(Signal, sid)
        if signal and not signal.processed:
            signal.processed = True
            signal.processed_at = datetime.utcnow()
            session.add(signal)

            # Update development record counters
            from app.services.development_records import mark_signal_processed

            mark_signal_processed(signal.child_id, session)

    session.commit()
