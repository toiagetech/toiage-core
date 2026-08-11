"""Questionnaire service — templates and responses."""

from datetime import datetime
from typing import Any

from sqlmodel import Session, select

from app.models.questionnaire import QuestionnaireResponse, QuestionnaireTemplate
from app.schemas.questionnaire import ChildContextOutput, QuestionnaireSubmit


# ─── Templates ────────────────────────────────────────────────────────


def create_template(body: dict, session: Session) -> QuestionnaireTemplate:
    """Create a new questionnaire template."""
    template = QuestionnaireTemplate(**body)
    session.add(template)
    session.commit()
    session.refresh(template)
    return template


def get_template(template_id: int, session: Session) -> QuestionnaireTemplate | None:
    """Get a template by ID."""
    return session.get(QuestionnaireTemplate, template_id)


def list_active_templates(session: Session) -> list[QuestionnaireTemplate]:
    """List all active questionnaire templates."""
    statement = select(QuestionnaireTemplate).where(QuestionnaireTemplate.is_active == True)
    return list(session.exec(statement).all())


def update_template(
    template_id: int, body: dict, session: Session
) -> QuestionnaireTemplate | None:
    """Update a questionnaire template."""
    template = session.get(QuestionnaireTemplate, template_id)
    if not template:
        return None

    update_data = {k: v for k, v in body.items() if hasattr(template, k)}
    for field, value in update_data.items():
        setattr(template, field, value)

    template.updated_at = datetime.utcnow()
    session.add(template)
    session.commit()
    session.refresh(template)
    return template


# ─── Responses ────────────────────────────────────────────────────────


def submit_questionnaire(
    body: QuestionnaireSubmit, session: Session
) -> QuestionnaireResponse:
    """Submit a questionnaire response for a child."""
    response = QuestionnaireResponse(
        child_id=body.child_id,
        parent_id=body.parent_id,
        template_id=body.template_id,
        responses=body.responses,
    )
    session.add(response)
    session.commit()
    session.refresh(response)

    # Derive structured child context from responses
    response.child_context = _convert_to_child_context(body.responses)
    session.add(response)
    session.commit()
    session.refresh(response)

    return response


def get_questionnaire_by_child(
    child_id: int, session: Session
) -> QuestionnaireResponse | None:
    """Get the latest questionnaire response for a child."""
    statement = (
        select(QuestionnaireResponse)
        .where(QuestionnaireResponse.child_id == child_id)
        .order_by(QuestionnaireResponse.completed_at.desc())
    )
    return session.exec(statement).first()


def get_questionnaire_response(
    response_id: int, session: Session
) -> QuestionnaireResponse | None:
    """Get a specific questionnaire response by ID."""
    return session.get(QuestionnaireResponse, response_id)


# ─── Helpers ──────────────────────────────────────────────────────────


def _convert_to_child_context(responses: list[dict[str, Any]]) -> dict[str, Any]:
    """Convert raw questionnaire responses into structured child context.

    This is a simplified version. In production, this would map each
    question ID to a structured field based on the template definition.
    """
    context: dict[str, Any] = {
        "interests": [],
        "parent_goals": [],
        "parent_concerns": [],
        "available_resources": [],
        "learning_style": [],
        "preferred_language": "en",
        "special_notes": None,
    }

    for item in responses:
        qid = item.get("question_id", "")
        answer = item.get("answer", "")

        if not answer:
            continue

        if qid == "age":
            try:
                context["age"] = int(answer)
            except (ValueError, TypeError):
                pass
        elif qid == "grade":
            context["grade"] = str(answer)
        elif qid == "interests":
            if isinstance(answer, list):
                context["interests"].extend(answer)
            else:
                context["interests"].append(str(answer))
        elif qid == "parent_goals":
            if isinstance(answer, list):
                context["parent_goals"].extend(answer)
            else:
                context["parent_goals"].append(str(answer))
        elif qid == "parent_concerns":
            if isinstance(answer, list):
                context["parent_concerns"].extend(answer)
            else:
                context["parent_concerns"].append(str(answer))
        elif qid == "available_resources":
            if isinstance(answer, list):
                context["available_resources"].extend(answer)
            else:
                context["available_resources"].append(str(answer))
        elif qid == "learning_style":
            if isinstance(answer, list):
                context["learning_style"].extend(answer)
            else:
                context["learning_style"].append(str(answer))
        elif qid == "preferred_language":
            context["preferred_language"] = str(answer)
        elif qid == "special_notes":
            context["special_notes"] = str(answer)

    return context


def convert_to_child_context_schema(
    context_dict: dict[str, Any],
) -> ChildContextOutput:
    """Convert a raw context dict to the ChildContextOutput schema."""
    return ChildContextOutput(**context_dict)
