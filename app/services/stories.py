"""Story generation service — generates a personalized story via LLM and saves it in one call.

Supports two flows:
1. Parent-selected generation (new): The parent chooses goal, mood, length,
   theme, and today's context. Uses the `stories/generate` prompt template.
2. Legacy generation: Uses age, theme, child_name, setting, word_count.
   Uses the `stories/create` prompt template.
"""

from sqlmodel import Session

from app.models.child import Child
from app.models.story import Story
from app.prompts import load_prompt
from app.schemas.story import StoryGenerateRequest
from app.services.analytics import EVENT_STORY_GENERATED, analytics
from app.services.llm.manager import llm_manager


# ── Helpers ─────────────────────────────────────────────────────────


def _length_to_word_count(story_length: str) -> str:
    """Map a story length label to an approximate word count."""
    mapping = {
        "short": "100",
        "medium": "200",
        "long": "400",
    }
    return mapping.get(story_length.lower(), "100")


def _age_to_age_group(age: str) -> str:
    """Derive a canonical age_group bucket from a numeric age string."""
    try:
        n = int(float(age))
    except (TypeError, ValueError):
        return "3-5"
    if n <= 5:
        return "3-5"
    if n <= 8:
        return "6-8"
    return "9-12"


def _build_today_context_section(today_context: str | None, child: Child | None) -> str:
    """Build the today's context section for the prompt."""
    parts: list[str] = []

    if today_context:
        parts.append(f"Today's context: {today_context}")

    if child:
        child_info = f"Child's name: {child.name}"
        if child.nick_name:
            child_info += f" (nickname: {child.nick_name})"
        if child.interests:
            child_info += f"\nChild's interests: {', '.join(child.interests)}"
        if child.special_notes:
            child_info += f"\nSpecial notes: {child.special_notes}"
        parts.append(child_info)

    if not parts:
        return ""

    return "\n".join(parts) + "\n"


def _parse_title_and_content(raw: str) -> tuple[str | None, str]:
    """Parse the LLM response to extract the title and content.

    The prompt asks for a title on the first line, then the story.
    If no clear title is found, returns (None, raw).
    """
    lines = raw.strip().splitlines()
    if not lines:
        return None, raw

    first = lines[0].strip()
    # If the first line looks like a title (short, no period at end)
    if first and len(first) < 100 and not first.endswith("."):
        # Remove common prefixes like "Title:" if present
        title = first.replace("Title:", "").strip()
        content = "\n".join(lines[1:]).strip()
        return title, content

    return None, raw.strip()


# ── Parent-selected generation (new) ────────────────────────────────


async def generate_story(body: StoryGenerateRequest, session: Session) -> Story:
    """Generate a personalized story via the LLM and persist it to the database.

    Uses the parent-selected parameters (goal, mood, length, theme, today's
    context) and optionally a child profile for personalization.

    Steps:
        1. Optionally load the child profile for personalization.
        2. Load the `stories/generate` prompt template and inject variables.
        3. Prepend the system prompt (tone/safety rules).
        4. Call the configured LLM provider via `llm_manager`.
        5. Parse the title and content from the LLM response.
        6. Save the generated story to the `stories` table.
        7. Emit the `story_generated` analytics event.

    Args:
        body: Generation request with parent-selected parameters.
        session: Database session.

    Returns:
        The saved `Story` row (with `id` and `created_at` populated). The LLM
        provenance (provider/model) is attached as transient attributes
        `story._provider` and `story._model` so the API layer can include them
        in the response without persisting them.
    """
    # 1 — optionally load child profile
    child: Child | None = None
    if body.child_id:
        child = session.get(Child, body.child_id)

    # 2 — build the today's context section
    today_context_section = _build_today_context_section(body.today_context, child)
    word_count = _length_to_word_count(body.story_length)

    # 3 — load template + inject system prompt
    prompt = load_prompt(
        "stories",
        "generate",
        {
            "goal": body.goal,
            "story_mood": body.story_mood,
            "story_length": body.story_length,
            "theme": body.theme,
            "today_context_section": today_context_section,
            "word_count": word_count,
        },
        inject_system=True,
        context="Generate a personalized story for a child based on parent-selected parameters",
    )

    # 4 — call the LLM
    result = await llm_manager.generate(
        prompt=prompt,
        provider=body.provider,
        temperature=body.temperature,
        max_tokens=body.max_tokens,
    )

    # 5 — parse title and content
    title, content = _parse_title_and_content(result.content)

    # 6 — persist
    story = Story(
        title=title,
        content=content,
        goal=body.goal,
        story_mood=body.story_mood,
        story_length=body.story_length,
        theme=body.theme,
        today_context=body.today_context,
    )
    session.add(story)
    session.commit()
    session.refresh(story)

    # 7 — analytics
    analytics.track(
        EVENT_STORY_GENERATED,
        properties={
            "story_id": story.id,
            "goal": story.goal,
            "story_mood": story.story_mood,
            "story_length": story.story_length,
            "theme": story.theme,
            "provider": result.provider,
            "model": result.model,
        },
    )

    # Attach LLM provenance as transient attrs (not persisted to the DB row)
    setattr(story, "_provider", result.provider)
    setattr(story, "_model", result.model)
    return story