"""Story generation and CRUD endpoints.

This is the business orchestration layer. It:
1. Validates the request
2. Loads the child profile (if provided) for personalization
3. Calls the education engine via HTTP to generate the story
4. Persists the result to the database
5. Returns the response

It never calls LLM providers directly — all AI generation is delegated to
toiage-education-engine.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from starlette import status

from app.db.session import get_session
from app.models.child import Child
from app.models.story import Story
from app.schemas.story import (
    StoryCreate,
    StoryGenerateRequest,
    StoryGenerateResponse,
    StoryRead,
)
from app.services.analytics import EVENT_STORY_GENERATED, analytics
from app.services.education_engine import generate_story as engine_generate_story
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
        "child profile for personalization. The story is generated via the education "
        "engine and persisted to the database in a single call."
    ),
    responses={
        422: {"description": "Validation error (missing required fields)"},
        400: {"description": "Invalid request or education engine error"},
        502: {"description": "Education engine unavailable"},
    },
)
async def generate_story_endpoint(
    body: StoryGenerateRequest,
    session: Session = Depends(get_session),
):
    """Generate a personalized story via the education engine and save it."""
    logger.info(
        "Story generation request received",
        extra={
            "endpoint": "POST /stories/generate",
            "request_payload": body.model_dump(by_alias=True),
            "child_id": body.child_id,
            "goal": body.goal,
            "story_mood": body.story_mood,
            "story_length": body.story_length,
            "theme": body.theme,
        },
    )

    # 1 — load child profile for personalization (if provided)
    child_profile = None
    if body.child_id:
        child = session.get(Child, body.child_id)
        if child:
            child_profile = {
                "name": child.name,
                "nick_name": child.nick_name,
                "interests": child.interests or [],
                "special_notes": child.special_notes,
                "preferred_language": child.preferred_language,
            }
            logger.info(
                "Child profile loaded for personalization",
                extra={"child_id": body.child_id, "child_name": child.name},
            )
        else:
            logger.warning(
                "Child profile not found — generating without personalization",
                extra={"child_id": body.child_id},
            )

    # 2 — build payload for the education engine
    payload = {
        "goal": body.goal,
        "story_mood": body.story_mood,
        "story_length": body.story_length,
        "theme": body.theme,
        "today_context": body.today_context,
        "language": body.language,
        "provider": body.provider,
        "temperature": body.temperature,
        "max_tokens": body.max_tokens,
        "child_profile": child_profile,
    }

    # 3 — call the education engine to generate the story
    try:
        result = await engine_generate_story(payload, session=session)
    except Exception as e:
        logger.error(
            "Story generation failed — education engine error",
            extra={"endpoint": "POST /stories/generate", "error": str(e)},
        )
        raise HTTPException(status_code=502, detail=f"Education engine error: {str(e)}")

    # 4 — persist to database
    story = Story(
        title=result.get("title"),
        content=result.get("content", ""),
        goal=result.get("goal"),
        story_mood=result.get("story_mood"),
        story_length=result.get("story_length"),
        theme=result.get("theme", body.theme),
        today_context=result.get("today_context"),
        language=result.get("language", "en"),
    )
    session.add(story)
    session.commit()
    session.refresh(story)

    logger.info(
        "Story saved to database",
        extra={
            "story_id": story.id,
            "title": story.title,
            "content_length": len(story.content) if story.content else 0,
            "language": story.language,
        },
    )

    # 5 — analytics
    analytics.track(
        EVENT_STORY_GENERATED,
        properties={
            "story_id": story.id,
            "goal": story.goal,
            "story_mood": story.story_mood,
            "story_length": story.story_length,
            "theme": story.theme,
            "language": story.language,
            "provider": result.get("provider", "unknown"),
            "model": result.get("model", "unknown"),
        },
    )

    # 6 — build response
    response = StoryGenerateResponse(
        id=story.id,
        title=story.title,
        content=story.content,
        goal=story.goal,
        story_mood=story.story_mood,
        story_length=story.story_length,
        theme=story.theme,
        today_context=story.today_context,
        language=story.language,
        created_at=story.created_at,
        provider=result.get("provider", body.provider),
        model=result.get("model", "unknown"),
    )

    logger.info(
        "Story generation response sent",
        extra={
            "endpoint": "POST /stories/generate",
            "story_id": response.id,
            "provider": response.provider,
            "model": response.model,
            "title": response.title,
            "content_length": len(response.content) if response.content else 0,
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