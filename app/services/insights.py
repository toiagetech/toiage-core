"""Insight service — generate and retrieve child insights."""

from datetime import datetime, timedelta
from typing import Any

from sqlmodel import Session, select

from app.models.development_record import ChildDevelopmentRecord
from app.models.insight import ChildInsight
from app.models.signal import Signal


# ─── Insight Generation ──────────────────────────────────────────────


def generate_insights(child_id: int, since: datetime | None, session: Session) -> list[ChildInsight]:
    """Generate new insights from unprocessed signals for a child.

    This is a deterministic rule-based implementation per the product docs.
    LLM may only assist with interpreting unstructured parent observations.
    """
    # Get unprocessed signals
    query = select(Signal).where(Signal.child_id == child_id, Signal.processed == False)  # noqa: E712
    if since:
        query = query.where(Signal.recorded_at >= since)
    signals = list(session.exec(query).all())

    if not signals:
        return []

    insights: list[ChildInsight] = []

    # Rule 1: Interest detection
    interest_signals = [s for s in signals if s.signal_type in ("play", "learning")]
    if interest_signals:
        categories = [s.category for s in interest_signals if s.category]
        if categories:
            from collections import Counter

            top = Counter(categories).most_common(3)
            for category, count in top:
                if count >= 2:
                    insight = ChildInsight(
                        child_id=child_id,
                        insight_type="preference",
                        category=category,
                        description=f"Shows repeated interest in {category}",
                        evidence=[{"signal_id": s.id, "data": s.data} for s in interest_signals if s.category == category],
                        confidence=min(0.9, 0.3 + (count * 0.15)),
                    )
                    session.add(insight)
                    insights.append(insight)

    # Rule 2: Parent observation interpretation (LLM-assisted placeholder)
    parent_signals = [s for s in signals if s.signal_type == "parent_observation"]
    for signal in parent_signals:
        note = str(signal.data.get("note", ""))
        if note:
            # In production, this would call an LLM to extract structured insights
            # For now, we store the raw observation as a strength
            insight = ChildInsight(
                child_id=child_id,
                insight_type="strength",
                category="observation",
                description=f"Parent noted: {note[:200]}",
                evidence=[{"signal_id": signal.id, "data": signal.data}],
                confidence=0.6,
            )
            session.add(insight)
            insights.append(insight)

    # Rule 3: Teacher feedback
    teacher_signals = [s for s in signals if s.signal_type == "teacher_feedback"]
    for signal in teacher_signals:
        feedback = str(signal.data.get("feedback", ""))
        if feedback:
            insight = ChildInsight(
                child_id=child_id,
                insight_type="strength",
                category="academic",
                description=f"Teacher feedback: {feedback[:200]}",
                evidence=[{"signal_id": signal.id, "data": signal.data}],
                confidence=0.7,
            )
            session.add(insight)
            insights.append(insight)

    # Mark signals as processed
    processed_ids = [s.id for s in signals]
    for sid in processed_ids:
        signal = session.get(Signal, sid)
        if signal:
            signal.processed = True
            signal.processed_at = datetime.utcnow()
            session.add(signal)

    # Update development record
    record = session.exec(
        select(ChildDevelopmentRecord).where(ChildDevelopmentRecord.child_id == child_id)
    ).first()
    if record:
        record.total_signals_processed += len(signals)
        record.last_signal_at = datetime.utcnow()
        record.last_insight_at = datetime.utcnow()
        record.updated_at = datetime.utcnow()
        session.add(record)

    session.commit()
    for insight in insights:
        session.refresh(insight)
    return insights


def get_insights_by_child(
    child_id: int, active_only: bool = True, session: Session = None
) -> list[ChildInsight]:
    """Get insights for a child."""
    query = select(ChildInsight).where(ChildInsight.child_id == child_id)
    if active_only:
        query = query.where(ChildInsight.is_active == True)  # noqa: E712
    query = query.order_by(ChildInsight.generated_at.desc())
    return list(session.exec(query).all())


def get_insight(insight_id: int, session: Session) -> ChildInsight | None:
    """Get a specific insight by ID."""
    return session.get(ChildInsight, insight_id)


def supersede_insight(insight_id: int, new_insight_id: int, session: Session) -> None:
    """Mark an insight as superseded by a newer one."""
    insight = session.get(ChildInsight, insight_id)
    if insight:
        insight.is_active = False
        insight.superseded_by_id = new_insight_id
        session.add(insight)
        session.commit()
