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
    try:
        story = await generate_story(body, session)
    except PromptNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Build response from the saved row + transient LLM provenance
    return StoryGenerateResponse(
        id=story.id,
        title=story.title,
        content=story.content,
        goal=story.goal,
        story_mood=story.story_mood,
        story_length=story.story_length,
        theme=story.theme,
        today_context=story.today_context,
        created_at=story.created_at,
        provider=getattr(story, "_provider", body.provider),
        model=getattr(story, "_model", "unknown"),
    )


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