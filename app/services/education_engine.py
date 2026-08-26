"""Integration point between toiage-core and AI generation.

Supports three modes controlled by the LLM_PROVIDER setting:
  - static:  Return a hardcoded mock response (no external dependencies).
  - db:      Fetch existing content from the toiage-core database.
  - *else*:  Call the toiage-education-engine via HTTP (openrouter, deepseek, etc.).
"""

import httpx
from sqlmodel import Session, select

from app.core.config import settings
from app.models.story import Story
from app.utils.logger import get_logger

logger = get_logger("app.education_engine")

# Timeout for generation calls (LLM calls can take a while)
_GENERATE_TIMEOUT = 120.0
_CONTEXT_TIMEOUT = 10.0


def _base_url() -> str:
    return settings.EDUCATION_ENGINE_URL.rstrip("/")


def _api_version() -> str:
    return getattr(settings, "EDUCATION_ENGINE_API_VERSION", "v1").lower()


async def _post_json(url: str, payload: dict, timeout: float) -> dict:
    """POST JSON to the education engine and return the response."""
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()


async def _generate(content_type: str, payload: dict, timeout: float) -> dict:
    """Generate via the engine, transparently supporting v1 and v2.

    v2 (/api/v2/generate) returns a shared core + a typed block named after
    the content type. This helper flattens that block back into the same flat
    shape the v1 endpoints return, so all callers stay unchanged regardless
    of which API version is configured.
    """
    if _api_version() == "v2":
        url = f"{_base_url()}/api/v2/generate"
        body = dict(payload)
        body.pop("type", None)
        body["type"] = content_type
        result = await _post_json(url, body, timeout)
        typed = result.pop(content_type, None)
        if isinstance(typed, dict):
            # Typed block wins; core fields (provider/model/language/status) fill gaps.
            flat = {**result, **typed}
        else:
            flat = {**result, **{k: v for k, v in (typed or {}).items()}}
        # Normalize id field name across versions.
        flat.setdefault("guidance_id", result.get("generate_id"))
        return flat

    # v1 — legacy per-type endpoints
    return await _post_json(f"{_base_url()}/api/v1/generate/{content_type}", payload, timeout)


# ─── Context fetching (existing, kept for backward compat) ──────────


async def fetch_project_context(grade: int, topic: str, subject: str = "") -> dict:
    """Fetch rich educational context for science project generation from the education engine."""
    if not settings.EDUCATION_ENGINE_ENABLED:
        logger.info("Education engine disabled — skipping context fetch")
        return _empty_project_context()

    url = f"{_base_url()}/api/v1/context/project?grade={grade}&topic={topic}"
    if subject:
        url += f"&subject={subject}"

    try:
        async with httpx.AsyncClient(timeout=_CONTEXT_TIMEOUT) as client:
            resp = await client.post(url)
            resp.raise_for_status()
            data = resp.json()
            logger.info(
                "Fetched project context from education engine",
                extra={"grade": grade, "topic": topic, "counts": data.get("counts", {})},
            )
            return data
    except Exception as e:
        logger.warning("Failed to fetch project context", extra={"error": str(e), "grade": grade, "topic": topic})
        return _empty_project_context()


async def fetch_assessment_context(grade: int, subject: str, chapter: str = "") -> dict:
    """Fetch context for teacher assessment generation."""
    if not settings.EDUCATION_ENGINE_ENABLED:
        return _empty_assessment_context()

    url = f"{_base_url()}/api/v1/context/assessment?grade={grade}&subject={subject}"
    if chapter:
        url += f"&chapter={chapter}"

    try:
        async with httpx.AsyncClient(timeout=_CONTEXT_TIMEOUT) as client:
            resp = await client.post(url)
            resp.raise_for_status()
            data = resp.json()
            logger.info(
                "Fetched assessment context from education engine",
                extra={"grade": grade, "subject": subject, "chapter": chapter, "counts": data.get("counts", {})},
            )
            return data
    except Exception as e:
        logger.warning("Failed to fetch assessment context", extra={"error": str(e)})
        return _empty_assessment_context()


# ─── Provider routing ────────────────────────────────────────────────

_LLM_PROVIDER = settings.LLM_PROVIDER.lower() if settings.LLM_PROVIDER else "openrouter"


def _is_static_mode() -> bool:
    return _LLM_PROVIDER == "static"


def _is_db_mode() -> bool:
    return _LLM_PROVIDER == "db"


# ─── Static / mock responses ────────────────────────────────────────


_MOCK_STORY = {
    "title": "The Brave Little Star",
    "content": (
        "Once upon a time, in a sky full of twinkling stars, there was a tiny star named Sparkle. "
        "Sparkle was small and often felt shy about shining. One night, a little boy looked up and said, "
        "\"Look at that beautiful star!\" That gave Sparkle courage. Sparkle twinkled brighter than ever, "
        "realizing that even the smallest light can make a big difference in someone's world."
    ),
    "goal": "courage",
    "story_mood": "bedtime",
    "story_length": "short",
    "theme": "space",
    "today_context": "The child was feeling shy about trying something new.",
    "language": "en",
    "provider": "static",
    "model": "static-mock-v1",
}

_MOCK_ACTIVITY = {
    "title": "Paper Airplane Adventure",
    "materials": ["Paper", "Crayons", "Tape"],
    "instructions": "Fold a paper airplane and decorate it. Fly it outside and observe how far it goes!",
    "challenge_question": "What makes the airplane fly farther?",
    "age_group": "4-6",
    "activity_mode": "outdoor",
    "provider": "static",
    "model": "static-mock-v1",
}

_MOCK_REFLECTION = {
    "message": "What a beautiful drawing! I can see you put a lot of thought into the colors.",
    "curiosity_question": "Why did you choose blue for the sky?",
    "provider": "static",
    "model": "static-mock-v1",
}

_MOCK_SCIENCE_PROJECT = {
    "project_title": "Growing a Bean in a Jar",
    "objective": "Observe how a bean plant grows from seed over two weeks.",
    "materials": ["Glass jar", "Paper towel", "Bean seed", "Water"],
    "instructions": "Place the paper towel inside the jar, add the bean, and keep it damp.",
    "difficulty": "easy",
    "budget": "low",
    "provider": "static",
    "model": "static-mock-v1",
}

_MOCK_ASSESSMENT = {
    "questions": [
        {"type": "mcq", "question": "What do plants need to grow?", "options": ["Sunlight", "Darkness", "Sand"], "answer": "Sunlight"},
        {"type": "short_answer", "question": "Name one source of water.", "answer": "Rain"},
    ],
    "grade": 2,
    "subject": "science",
    "provider": "static",
    "model": "static-mock-v1",
}


# ─── DB-mode helpers ─────────────────────────────────────────────────


def _fetch_story_from_db(session: Session | None, payload: dict) -> dict | None:
    """Try to find an existing story in the database matching the request criteria."""
    if session is None:
        return None
    query = select(Story)
    if payload.get("theme"):
        query = query.where(Story.theme == payload["theme"])
    if payload.get("goal"):
        query = query.where(Story.goal == payload["goal"])
    if payload.get("story_mood"):
        query = query.where(Story.story_mood == payload["story_mood"])
    if payload.get("story_length"):
        query = query.where(Story.story_length == payload["story_length"])
    if payload.get("language"):
        query = query.where(Story.language == payload["language"])
    query = query.order_by(Story.created_at.desc()).limit(1)
    story = session.exec(query).first()
    if story is None:
        return None
    return {
        "title": story.title,
        "content": story.content,
        "goal": story.goal,
        "story_mood": story.story_mood,
        "story_length": story.story_length,
        "theme": story.theme,
        "today_context": story.today_context,
        "language": story.language,
        "provider": "db",
        "model": "db-retrieval-v1",
    }


# ─── AI Generation calls with provider routing ──────────────────────


async def generate_story(payload: dict, session: Session | None = None) -> dict:
    """Generate or retrieve a story based on LLM_PROVIDER setting.

    Modes:
      - static:  Return a hardcoded mock story.
      - db:      Look up an existing story in the database.
      - *else*:  Call the education engine via HTTP.

    Args:
        payload: Story generation request parameters.
        session: Optional SQLModel Session (required for db mode).

    Returns:
        Dict with: title, content, goal, story_mood, story_length, theme,
        today_context, language, provider, model
    """
    if _is_static_mode():
        logger.info("Story generation — using static mock response")
        return dict(_MOCK_STORY)

    if _is_db_mode():
        logger.info(
            "Story generation — attempting database lookup",
            extra={"theme": payload.get("theme"), "goal": payload.get("goal")},
        )
        found = _fetch_story_from_db(session, payload)
        if found:
            logger.info("Story generation — found matching story in DB", extra={"story_title": found.get("title")})
            return found
        logger.warning("Story generation — no matching story found in DB, falling back to static mock")
        return dict(_MOCK_STORY)

    # Default: call education engine
    try:
        result = await _generate("story", payload, _GENERATE_TIMEOUT)
        logger.info(
            "Story generated via education engine",
            extra={"provider": result.get("provider"), "model": result.get("model"), "language": result.get("language")},
        )
        return result
    except httpx.HTTPStatusError as e:
        logger.error("Education engine returned error for story generation", extra={"status": e.response.status_code, "detail": e.response.text[:200]})
        raise
    except Exception as e:
        logger.error("Failed to call education engine for story generation", extra={"error": str(e)})
        raise


async def generate_activity(payload: dict, session: Session | None = None) -> dict:
    """Generate or retrieve an activity based on LLM_PROVIDER setting.

    Modes:
      - static:  Return a hardcoded mock activity.
      - db:      Currently falls back to static (no activity table lookup yet).
      - *else*:  Call the education engine via HTTP.
    """
    if _is_static_mode():
        logger.info("Activity generation — using static mock response")
        return dict(_MOCK_ACTIVITY)

    if _is_db_mode():
        logger.info("Activity generation — db mode (fallback to static)")
        return dict(_MOCK_ACTIVITY)

    try:
        result = await _generate("activity", payload, _GENERATE_TIMEOUT)
        logger.info(
            "Activity generated via education engine",
            extra={"provider": result.get("provider"), "model": result.get("model")},
        )
        return result
    except httpx.HTTPStatusError as e:
        logger.error("Education engine returned error for activity generation", extra={"status": e.response.status_code, "detail": e.response.text[:200]})
        raise
    except Exception as e:
        logger.error("Failed to call education engine for activity generation", extra={"error": str(e)})
        raise


async def generate_reflection(payload: dict, session: Session | None = None) -> dict:
    """Generate a reflection based on LLM_PROVIDER setting.

    Modes:
      - static:  Return a hardcoded mock reflection.
      - db:      Fallback to static (no reflection table yet).
      - *else*:  Call the education engine via HTTP.
    """
    if _is_static_mode():
        logger.info("Reflection generation — using static mock response")
        return dict(_MOCK_REFLECTION)

    if _is_db_mode():
        logger.info("Reflection generation — db mode (fallback to static)")
        return dict(_MOCK_REFLECTION)

    try:
        result = await _generate("reflection", payload, _GENERATE_TIMEOUT)
        logger.info(
            "Reflection generated via education engine",
            extra={"provider": result.get("provider"), "model": result.get("model")},
        )
        return result
    except httpx.HTTPStatusError as e:
        logger.error("Education engine returned error for reflection generation", extra={"status": e.response.status_code, "detail": e.response.text[:200]})
        raise
    except Exception as e:
        logger.error("Failed to call education engine for reflection generation", extra={"error": str(e)})
        raise


async def generate_science_project(payload: dict, session: Session | None = None) -> dict:
    """Generate a science project based on LLM_PROVIDER setting.

    Modes:
      - static:  Return a hardcoded mock science project.
      - db:      Fallback to static (no project table lookup yet).
      - *else*:  Call the education engine via HTTP.
    """
    if _is_static_mode():
        logger.info("Science project generation — using static mock response")
        return dict(_MOCK_SCIENCE_PROJECT)

    if _is_db_mode():
        logger.info("Science project generation — db mode (fallback to static)")
        return dict(_MOCK_SCIENCE_PROJECT)

    url = f"{_base_url()}/api/v1/generate/science-project"
    try:
        result = await _post_json(url, payload, _GENERATE_TIMEOUT)
        logger.info(
            "Science project generated via education engine",
            extra={"project_title": result.get("project_title"), "provider": result.get("provider")},
        )
        return result
    except httpx.HTTPStatusError as e:
        logger.error("Education engine returned error for science project generation", extra={"status": e.response.status_code, "detail": e.response.text[:200]})
        raise
    except Exception as e:
        logger.error("Failed to call education engine for science project generation", extra={"error": str(e)})
        raise


async def generate_assessment(payload: dict, session: Session | None = None) -> dict:
    """Generate an assessment based on LLM_PROVIDER setting.

    Modes:
      - static:  Return a hardcoded mock assessment.
      - db:      Fallback to static (no assessment table lookup yet).
      - *else*:  Call the education engine via HTTP.
    """
    if _is_static_mode():
        logger.info("Assessment generation — using static mock response")
        return dict(_MOCK_ASSESSMENT)

    if _is_db_mode():
        logger.info("Assessment generation — db mode (fallback to static)")
        return dict(_MOCK_ASSESSMENT)

    try:
        result = await _generate("assessment", payload, _GENERATE_TIMEOUT)
        logger.info(
            "Assessment generated via education engine",
            extra={"grade": result.get("grade"), "subject": result.get("subject"), "provider": result.get("provider")},
        )
        return result
    except httpx.HTTPStatusError as e:
        logger.error("Education engine returned error for assessment generation", extra={"status": e.response.status_code, "detail": e.response.text[:200]})
        raise
    except Exception as e:
        logger.error("Failed to call education engine for assessment generation", extra={"error": str(e)})
        raise


async def generate_guidance(payload: dict, session: Session | None = None) -> dict:
    """Generate parent-friendly guidance via the education engine.

    Runs the shared Knowledge Agent → Wisdom Agent → Guidance Service → LLM
    flow, with metadata-aware RAG retrieval (age-band + domain filtered).

    Payload: question (required), child_profile {name, age}, language, provider.
    Returns flat dict: guidance, resources[], suggested_next[], parent_tips[],
    question, normalized_intent/topic, provider, model.
    """
    if _is_static_mode():
        logger.info("Guidance generation — using static mock response")
        return {
            "guidance_id": "static-guidance",
            "status": "COMPLETED",
            "question": payload.get("question", ""),
            "guidance": "Static guidance response.",
            "resources": [],
            "suggested_next": [],
            "parent_tips": [],
            "provider": "mock",
        }

    try:
        result = await _generate("guidance", payload, _GENERATE_TIMEOUT)
        logger.info(
            "Guidance generated via education engine",
            extra={
                "provider": result.get("provider"),
                "model": result.get("model"),
                "resources": len(result.get("resources") or []),
            },
        )
        return result
    except httpx.HTTPStatusError as e:
        logger.error("Education engine returned error for guidance generation", extra={"status": e.response.status_code, "detail": e.response.text[:200]})
        raise
    except Exception as e:
        logger.error("Failed to call education engine for guidance generation", extra={"error": str(e)})
        raise


# ─── Helpers (kept for backward compat) ─────────────────────────────


def _format_context_for_prompt(context: dict, context_type: str = "project") -> str:
    """Format context dict into a readable string for injection into LLM prompts.

    NOTE: This is no longer needed since the education engine handles prompt
    building internally. Kept for backward compatibility.
    """
    parts = []

    if context_type == "project":
        if context.get("curriculum"):
            parts.append("### Curriculum Context")
            for c in context["curriculum"][:5]:
                parts.append(f"- {c.get('subject', '')}: {c.get('chapter', '')} → {c.get('topic', '')}")

        if context.get("innovations"):
            parts.append("\n### Real-World Innovations")
            for i in context["innovations"][:3]:
                parts.append(f"- {i.get('title', '')} ({i.get('organization', '')}): {i.get('summary', '')[:200]}")

        if context.get("project_references"):
            parts.append("\n### Similar Project References")
            for r in context["project_references"][:3]:
                parts.append(f"- {r.get('title', '')} (Difficulty: {r.get('difficulty', '')})")

        if context.get("knowledge_chunks"):
            parts.append("\n### Knowledge Base Excerpts")
            for k in context["knowledge_chunks"][:3]:
                parts.append(f"- {k.get('text', '')[:300]}")

    elif context_type == "assessment":
        if context.get("curriculum"):
            parts.append("### Curriculum Context")
            for c in context["curriculum"][:5]:
                parts.append(f"- {c.get('subject', '')}: {c.get('chapter', '')} → {c.get('topic', '')}")

        if context.get("knowledge_chunks"):
            parts.append("\n### Reference Material")
            for k in context["knowledge_chunks"][:3]:
                parts.append(f"- {k.get('text', '')[:300]}")

    return "\n".join(parts)


def _empty_project_context() -> dict:
    return {"curriculum": [], "innovations": [], "project_references": [], "knowledge_chunks": [], "counts": {}}


def _empty_assessment_context() -> dict:
    return {"curriculum": [], "knowledge_chunks": [], "counts": {}}