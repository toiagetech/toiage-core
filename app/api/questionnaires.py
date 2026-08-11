"""Questionnaire endpoints — templates and parent responses."""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from starlette import status

from app.db.session import get_session
from app.schemas.questionnaire import (
    ChildContextOutput,
    QuestionnaireResponseRead,
    QuestionnaireSubmit,
    QuestionnaireTemplateCreate,
    QuestionnaireTemplateRead,
    QuestionnaireTemplateUpdate,
)
from app.services.questionnaires import (
    convert_to_child_context_schema,
    create_template,
    get_questionnaire_by_child,
    get_questionnaire_response,
    get_template,
    list_active_templates,
    submit_questionnaire,
    update_template,
)

router = APIRouter(prefix="/questionnaires", tags=["questionnaires"])


# ─── Templates ────────────────────────────────────────────────────────


@router.post(
    "/templates",
    response_model=QuestionnaireTemplateRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a questionnaire template",
    description="Create a new admin-defined questionnaire template.",
    responses={422: {"description": "Validation error"}},
)
async def create_template_endpoint(
    body: QuestionnaireTemplateCreate,
    session: Session = Depends(get_session),
):
    """Create a questionnaire template."""
    payload = body.model_dump()
    return create_template(payload, session)


@router.get(
    "/templates",
    response_model=list[QuestionnaireTemplateRead],
    summary="List active questionnaire templates",
    description="Retrieve all active questionnaire templates.",
)
async def list_templates_endpoint(session: Session = Depends(get_session)):
    """List all active templates."""
    return list_active_templates(session)


@router.get(
    "/templates/{template_id}",
    response_model=QuestionnaireTemplateRead,
    summary="Get a questionnaire template",
    description="Retrieve a single template by ID.",
    responses={404: {"description": "Template not found"}},
)
async def get_template_endpoint(template_id: int, session: Session = Depends(get_session)):
    """Get a template by ID."""
    template = get_template(template_id, session)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.put(
    "/templates/{template_id}",
    response_model=QuestionnaireTemplateRead,
    summary="Update a questionnaire template",
    description="Update an existing template (partial update).",
    responses={404: {"description": "Template not found"}},
)
async def update_template_endpoint(
    template_id: int,
    body: QuestionnaireTemplateUpdate,
    session: Session = Depends(get_session),
):
    """Update a template."""
    payload = body.model_dump(exclude_unset=True)
    template = update_template(template_id, payload, session)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


# ─── Responses ────────────────────────────────────────────────────────


@router.post(
    "/submit",
    response_model=QuestionnaireResponseRead,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a questionnaire response",
    description="Submit parent answers for a child and derive structured child context.",
    responses={422: {"description": "Validation error"}},
)
async def submit_questionnaire_endpoint(
    body: QuestionnaireSubmit,
    session: Session = Depends(get_session),
):
    """Submit a questionnaire response."""
    return submit_questionnaire(body, session)


@router.get(
    "/{child_id}",
    response_model=QuestionnaireResponseRead,
    summary="Get questionnaire response for a child",
    description="Retrieve the latest questionnaire response for a child.",
    responses={404: {"description": "No response found"}},
)
async def get_questionnaire_endpoint(child_id: int, session: Session = Depends(get_session)):
    """Get the latest response for a child."""
    response = get_questionnaire_by_child(child_id, session)
    if not response:
        raise HTTPException(status_code=404, detail="No questionnaire response found")
    return response


@router.get(
    "/{child_id}/context",
    response_model=ChildContextOutput,
    summary="Get structured child context from questionnaire",
    description="Return the derived structured context for use by the education engine.",
    responses={404: {"description": "No response found"}},
)
async def get_child_context_endpoint(child_id: int, session: Session = Depends(get_session)):
    """Get structured child context derived from questionnaire."""
    response = get_questionnaire_by_child(child_id, session)
    if not response or not response.child_context:
        raise HTTPException(status_code=404, detail="No child context available")
    return convert_to_child_context_schema(response.child_context)
