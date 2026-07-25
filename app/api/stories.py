"""Story generation and CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from starlette import status

from app.db.session import get_session
from app.models.story import Story
from app.prompts import PromptNotFoundError
from app.schemas.story import (
    StoryCreate,
    StoryGenerateRequest,
    StoryGenerateResponse,
    StoryRead,
)
from app.services.analytics import EVENT_STORY_GENERATED, analytics
from app.services.stories import generate_story
from app.utils.logger import get_logger

logger = get_logger("app.api.stories")

router = APIRouter(prefix="/stories", tags=["stories"])


@router.post(
    "/generate",
    response_model=StoryGenerateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a personalized AI story",
    description=(
        "Generate a personalized, age-appropriate story based on parent-selected "
        "parameters (goal, mood, length, theme, today's context) and optionally a "
        "child profile for personalization. The story is generated via the LLM and "
        "persisted to the database in a single call. "
        "Provider defaults to 'mock' (no API key required); set provider='openrouter' "
        "to use the real model."
    ),
    responses={
        404: {"description": "Prompt template not found"},
        422: {"description": "Validation error (missing required fields)"},
        400: {"description": "Invalid request (e.g., unknown LLM provider)"},
    },
)
async def generate_story_endpoint(
    body: StoryGenerateRequest,
    session: Session = Depends(get_session),
):
    """Generate a personalized story via the LLM and save it."""
    # ── Log incoming request payload ──
    logger.info(
        "Story generation request received",
        extra={
            "endpoint": "POST /stories/generate",
            "request_payload": body.model_dump(by_alias=True),
            "child_id": body.child_id,
            "provider": body.provider,
            "goal": body.goal,
            "story_mood": body.story_mood,
            "story_length": body.story_length,
            "theme": body.theme,
            "temperature": body.temperature,
            "max_tokens": body.max_tokens,
        },
    )

    try:
        story = await generate_story(body, session)
    except PromptNotFoundError as e:
        logger.error(
            "Story generation failed — prompt template not found",
            extra={"endpoint": "POST /stories/generate", "error": str(e)},
        )
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        logger.error(
            "Story generation failed — invalid request",
            extra={"endpoint": "POST /stories/generate", "error": str(e)},
        )
        raise HTTPException(status_code=400, detail=str(e))

    # Build response from the saved row + transient LLM provenance
    response = StoryGenerateResponse(
        id=story.id,
        title=story.title,
        content=story.content,
        goal=story.goal,
        story_mood=story.story_mood,
        story_length=story.story_length,
        theme=story.theme,
        today_context=story.today_context,
        language=getattr(story, "language", "en"),
        created_at=story.created_at,
        provider=getattr(story, "_provider", body.provider),
        model=getattr(story, "_model", "unknown"),
    )

    # ── Log final response payload ──
    logger.info(
        "Story generation response sent",
        extra={
            "endpoint": "POST /stories/generate",
            "story_id": response.id,
            "provider": response.provider,
            "model": response.model,
            "title": response.title,
            "content_length": len(response.content) if response.content else 0,
            "content_preview": (response.content[:200] + "...") if response.content and len(response.content) > 200 else response.content,
        },
    )

    return response


@router.post(
    "",
    response_model=StoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a story (legacy)",
    description="Save a new story to the database. The story content should be generated beforehand, or use POST /stories/generate to do both in one call.",
    responses={
        422: {"description": "Validation error (missing required fields)"},
    },
)
async def create_story(body: StoryCreate, session: Session = Depends(get_session)):
    """Create and save a new story (legacy flow)."""
    story = Story(
        content=body.content,
        age_group=body.age_group,
        theme=body.theme,
        skills=body.skills,
        difficulty=body.difficulty,
    )
    session.add(story)
    session.commit()
    session.refresh(story)
    analytics.track(
        EVENT_STORY_GENERATED,
        properties={
            "story_id": story.id,
            "age_group": story.age_group,
            "theme": story.theme,
            "difficulty": story.difficulty,
        },
    )
    return story


@router.get(
    "/{story_id}",
    response_model=StoryRead,
    summary="Get story by ID",
    description="Retrieve a single story by its unique identifier.",
    responses={
        404: {"description": "Story not found"},
    },
)
async def get_story(story_id: int, session: Session = Depends(get_session)):
    """Retrieve a single story by ID."""
    story = session.get(Story, story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    return story


@router.get(
    "",
    response_model=list[StoryRead],
    summary="List all stories",
    description="Retrieve all stories ordered by creation date (newest first).",
)
async def list_stories(session: Session = Depends(get_session)):
    """List all stories."""
    stories = session.exec(select(Story).order_by(Story.created_at.desc())).all()
    return stories