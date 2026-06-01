"""Client for the Toiage Education Engine — fetches curriculum context, knowledge chunks, and more."""

import httpx

from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger("app.education_engine")


def _base_url() -> str:
    return settings.EDUCATION_ENGINE_URL.rstrip("/")


async def fetch_project_context(grade: int, topic: str, subject: str = "") -> dict:
    """Fetch rich educational context for science project generation from the education engine."""
    if not settings.EDUCATION_ENGINE_ENABLED:
        logger.info("Education engine disabled — skipping context fetch")
        return _empty_project_context()

    url = f"{_base_url()}/api/v1/context/project?grade={grade}&topic={topic}"
    if subject:
        url += f"&subject={subject}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
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
        async with httpx.AsyncClient(timeout=10.0) as client:
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


def _format_context_for_prompt(context: dict, context_type: str = "project") -> str:
    """Format context dict into a readable string for injection into LLM prompts."""
    parts = []

    if context_type == "project":
        # Curriculum
        if context.get("curriculum"):
            parts.append("### Curriculum Context")
            for c in context["curriculum"][:5]:
                parts.append(f"- {c.get('subject', '')}: {c.get('chapter', '')} → {c.get('topic', '')}")

        # Innovations
        if context.get("innovations"):
            parts.append("\n### Real-World Innovations")
            for i in context["innovations"][:3]:
                parts.append(f"- {i.get('title', '')} ({i.get('organization', '')}): {i.get('summary', '')[:200]}")

        # Project references
        if context.get("project_references"):
            parts.append("\n### Similar Project References")
            for r in context["project_references"][:3]:
                parts.append(f"- {r.get('title', '')} (Difficulty: {r.get('difficulty', '')})")

        # Knowledge chunks
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