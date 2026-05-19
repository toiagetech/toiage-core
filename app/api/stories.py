from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db.session import get_session
from app.models.story import Story
from app.schemas.story import StoryCreate, StoryRead
from app.services.analytics import EVENT_STORY_GENERATED, analytics

router = APIRouter(prefix="/stories", tags=["stories"])


@router.post("", response_model=StoryRead, status_code=201)
async def create_story(body: StoryCreate, session: Session = Depends(get_session)):
    """Create and save a new story."""
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


@router.get("/{story_id}", response_model=StoryRead)
async def get_story(story_id: int, session: Session = Depends(get_session)):
    """Retrieve a single story by ID."""
    story = session.get(Story, story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    return story


@router.get("", response_model=list[StoryRead])
async def list_stories(session: Session = Depends(get_session)):
    """List all stories."""
    stories = session.exec(select(Story).order_by(Story.created_at.desc())).all()
    return stories