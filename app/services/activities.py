import re

from sqlmodel import Session, select

from app.models.activity import Activity
from app.models.story import Story
from app.prompts import load_prompt
from app.schemas.activity import ActivityGenerateRequest
from app.services.analytics import EVENT_ACTIVITY_GENERATED, analytics
from app.services.llm.manager import llm_manager


def _resolve_story_text(body: ActivityGenerateRequest, session: Session) -> str:
    """Get story text from request, preferring story_id lookup."""
    if body.story_id:
        story = session.get(Story, body.story_id)
        if not story:
            raise ValueError(f"Story not found: id={body.story_id}")
        return story.content
    if body.story_text:
        return body.story_text
    raise ValueError("Either story_id or story_text is required")


def _parse_llm_output(text: str) -> dict:
    """Parse structured LLM output into fields."""
    title = ""
    materials = ""
    instructions = ""
    challenge_question = ""

    title_match = re.search(r"Title:\s*(.+?)(?:\n|$)", text)
    if title_match:
        title = title_match.group(1).strip()

    mat_match = re.search(r"Materials:\s*(.+?)(?=\nInstructions:)", text, re.DOTALL)
    if mat_match:
        materials = mat_match.group(1).strip()

    instr_match = re.search(
        r"Instructions:\s*(.+?)(?=\nChallenge Question:)", text, re.DOTALL
    )
    if instr_match:
        instructions = instr_match.group(1).strip()

    cq_match = re.search(r"Challenge Question:\s*(.+)", text, re.DOTALL)
    if cq_match:
        challenge_question = cq_match.group(1).strip()

    return {
        "title": title or "Creative Activity",
        "materials": materials or "- Paper\n- Crayons\n- Glue\n- Scissors\n- Imagination!",
        "instructions": instructions or "1. Gather your materials.\n2. Use your creativity!\n3. Have fun and share your creation.",
        "challenge_question": challenge_question or "What would you create next?",
    }


async def generate_activity(
    body: ActivityGenerateRequest, session: Session
) -> Activity:
    """Generate a hands-on activity from a story and save it."""
    story_text = _resolve_story_text(body, session)

    prompt = load_prompt(
        "activities",
        "generate",
        {
            "age_group": body.age_group,
            "story_text": story_text,
            "activity_mode": body.activity_mode,
        },
        inject_system=True,
        age_group=body.age_group,
        context="Generate a hands-on activity from a story",
    )

    result = await llm_manager.generate(
        prompt=prompt,
        provider=body.provider,
        temperature=0.7,
        max_tokens=1024,
    )

    parsed = _parse_llm_output(result.content)

    activity = Activity(
        story_id=body.story_id,
        title=parsed["title"],
        materials=parsed["materials"],
        instructions=parsed["instructions"],
        challenge_question=parsed["challenge_question"],
        age_group=body.age_group,
        activity_mode=body.activity_mode,
    )
    session.add(activity)
    session.commit()
    session.refresh(activity)
    analytics.track(
        EVENT_ACTIVITY_GENERATED,
        properties={
            "activity_id": activity.id,
            "story_id": body.story_id,
            "age_group": body.age_group,
            "activity_mode": body.activity_mode,
        },
    )
    return activity