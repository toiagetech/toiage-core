"""Story generation service — generates a personalized story via LLM and saves it in one call.

Supports two flows:
1. Parent-selected generation (new): The parent chooses goal, mood, length,
   theme, and optional today's context. Uses the `stories/generate` prompt template.
2. Legacy generation: Uses age, theme, child_name, setting, word_count.
   Uses the `stories/create` prompt template.
"""

from sqlmodel import Session

from app.core.config import settings
from app.models.child import Child
from app.models.story import Story
from app.prompts import load_prompt
from app.schemas.story import StoryGenerateRequest
from app.services.analytics import EVENT_STORY_GENERATED, analytics
from app.services.llm.manager import llm_manager
from app.utils.logger import get_logger

logger = get_logger("app.services.stories")


# ── Language mapping ────────────────────────────────────────────────

# Maps ISO 639-1 language codes to human-readable language names.
# Used in the prompt template so the LLM knows which language to write in.
LANGUAGE_MAP: dict[str, str] = {
    "en": "English",
    "hi": "Hindi",
    "bn": "Bengali",
    "ta": "Tamil",
    "te": "Telugu",
    "mr": "Marathi",
    "gu": "Gujarati",
    "kn": "Kannada",
    "ml": "Malayalam",
    "pa": "Punjabi",
    "ur": "Urdu",
    "or": "Odia",
    "sa": "Sanskrit",
}


def _language_code_to_name(code: str) -> str:
    """Convert a language code (e.g. 'hi') to a language name (e.g. 'Hindi').

    Falls back to the code itself if not found in the map.
    """
    return LANGUAGE_MAP.get(code, code)


def _resolve_language(body: StoryGenerateRequest, child: Child | None) -> str:
    """Resolve the language to use for the story.

    Priority:
      1. body.language (explicit selection from the UI — overrides child profile)
      2. child.preferred_language (saved in the child profile)
      3. "en" (default fallback)
    """
    # 1 — explicit selection from the request
    if body.language and body.language in LANGUAGE_MAP:
        return body.language

    # 2 — child profile preferred language
    if child and child.preferred_language and child.preferred_language in LANGUAGE_MAP:
        return child.preferred_language

    # 3 — default
    return "en"


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
        2. Resolve the language (explicit > child profile > default).
        3. Load the `stories/generate` prompt template and inject variables.
        4. Prepend the system prompt (tone/safety rules).
        5. Call the configured LLM provider via `llm_manager` (or fetch from DB).
        6. Parse the title and content from the LLM response.
        7. Save the generated story to the `stories` table.
        8. Emit the `story_generated` analytics event.

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
        if child:
            logger.info(
                "Child profile loaded for personalization",
                extra={
                    "child_id": body.child_id,
                    "child_name": child.name,
                    "child_nick_name": child.nick_name,
                    "child_interests": child.interests,
                    "child_special_notes": child.special_notes,
                    "child_preferred_language": child.preferred_language,
                },
            )
        else:
            logger.warning(
                "Child profile not found — generating without personalization",
                extra={"child_id": body.child_id},
            )
    else:
        logger.info("No child_id provided — generating without personalization")

    # 2 — resolve language (explicit > child profile > default)
    resolved_language = _resolve_language(body, child)
    language_name = _language_code_to_name(resolved_language)
    logger.info(
        "Language resolved for story",
        extra={
            "requested_language": body.language,
            "child_preferred_language": child.preferred_language if child else None,
            "resolved_language": resolved_language,
            "language_name": language_name,
        },
    )

    # 3 — build the today's context section
    today_context_section = _build_today_context_section(body.today_context, child)
    word_count = _length_to_word_count(body.story_length)

    # 4 — load template + inject system prompt
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
            "language_name": language_name,
        },
        inject_system=True,
        context="Generate a personalized story for a child based on parent-selected parameters",
    )

    logger.info(
        "Prompt built for LLM",
        extra={
            "prompt_template": "stories/generate",
            "word_count_target": word_count,
            "language": resolved_language,
            "language_name": language_name,
            "prompt_length": len(prompt),
            "prompt_preview": prompt[:200],
        },
    )

    # 5 — call the LLM (or fetch from DB if provider is "db")
    #
    # Provider modes:
    #   "mock"      → static canned response (no API key, no DB)
    #   "openrouter" → real AI model via OpenRouter API (costs money)
    #   "db"        → fetch an existing story from the database (saves API cost)
    #                  Falls back to LLM if no matching story is found.
    provider = settings.LLM_PROVIDER
    logger.info(
        "Calling LLM",
        extra={
            "provider": provider,
            "temperature": body.temperature,
            "max_tokens": body.max_tokens,
        },
    )

    if provider == "db":
        # ── DB mode: fetch an existing story instead of calling the LLM ──
        # Try to find a story in the DB that matches the request parameters
        # (including language) to save API costs by reusing previously
        # generated stories.
        from sqlmodel import select as _select

        _query = _select(Story).where(
            Story.goal == body.goal,
            Story.theme == body.theme,
            Story.language == resolved_language,
        )
        if body.story_mood:
            _query = _query.where(Story.story_mood == body.story_mood)
        if body.story_length:
            _query = _query.where(Story.story_length == body.story_length)
        _query = _query.order_by(Story.created_at.desc()).limit(1)

        _existing = session.exec(_query).first()
        if _existing:
            logger.info(
                "Story fetched from database (db mode — no LLM call)",
                extra={
                    "story_id": _existing.id,
                    "title": _existing.title,
                    "goal": _existing.goal,
                    "theme": _existing.theme,
                    "language": _existing.language,
                },
            )
            # Attach provenance as transient attrs
            setattr(_existing, "_provider", "db")
            setattr(_existing, "_model", "db-fetch")
            return _existing

        # No matching story found — fall back to the configured LLM
        logger.info(
            "No matching story in DB — falling back to LLM",
            extra={"fallback_provider": settings.LLM_PROVIDER, "language": resolved_language},
        )
        provider = settings.LLM_PROVIDER

    result = await llm_manager.generate(
        prompt=prompt,
        provider=provider,
        temperature=body.temperature,
        max_tokens=body.max_tokens,
    )

    logger.info(
        "LLM response received",
        extra={
            "provider": result.provider,
            "model": result.model,
            "response_length": len(result.content) if result.content else 0,
            "response_preview": (result.content[:200] + "...") if result.content and len(result.content) > 200 else result.content,
            "usage": result.usage,
        },
    )

    # 6 — parse title and content
    title, content = _parse_title_and_content(result.content)
    logger.info(
        "Parsed title and content from LLM response",
        extra={
            "title": title,
            "content_length": len(content) if content else 0,
        },
    )

    # 7 — persist
    story = Story(
        title=title,
        content=content,
        goal=body.goal,
        story_mood=body.story_mood,
        story_length=body.story_length,
        theme=body.theme,
        today_context=body.today_context,
        language=resolved_language,
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
            "goal": story.goal,
            "theme": story.theme,
            "language": story.language,
        },
    )

    # 8 — analytics
    analytics.track(
        EVENT_STORY_GENERATED,
        properties={
            "story_id": story.id,
            "goal": story.goal,
            "story_mood": story.story_mood,
            "story_length": story.story_length,
            "theme": story.theme,
            "language": story.language,
            "provider": result.provider,
            "model": result.model,
        },
    )

    # Attach LLM provenance as transient attrs (not persisted to the DB row)
    setattr(story, "_provider", result.provider)
    setattr(story, "_model", result.model)
    return story