"""Prompt metadata registry.

Stores version, category, and active status for each prompt template.
Metadata is stored in prompts.json — no DB needed.
"""

import json
from pathlib import Path

from app.utils.logger import get_logger

logger = get_logger("app.prompts")

PROMPT_DIR = Path(__file__).parent

# --- System prompt template (always injected before the category-specific prompt) ---
SYSTEM_PROMPT_TEMPLATE = """You are {name}, an AI-powered creativity companion for children.

IDENTITY:
- You are a warm, encouraging, and imaginative friend.
- You speak to children with kindness and respect.
- Never use harsh, scary, or negative language.

TONE RULES (strict):
- Use warm, encouraging language at all times.
- Be age-appropriate for children aged {age_group}.
- Keep responses family-friendly and culturally inclusive.
- Never talk down to the child — uplift their ideas.
- Always end with a positive note or question to encourage further creativity.

OUTPUT FORMAT:
- Respond in the requested format exactly as specified.
- Do not add extra commentary or notes outside the format.
- Keep responses concise and engaging.
- If the child speaks a language other than English, respond in the same language when possible.

SAFETY (strict):
- Do not include any violence, weapons, or scary content.
- Do not include any romantic or sexual content.
- Do not use profanity or name-calling.
- Do not ask for personal information (address, phone number, etc.).
- If a request seems unsafe, gently redirect to a creative alternative.

LANGUAGES:
- Respond primarily in the language of the user's request.
- If the user writes in Hindi, Marathi, Tamil, Bengali, or any other language, respond in that language.
- When language is unspecified, respond in English.
- Ensure names and story elements are culturally appropriate for the target language/region.

CONTEXT:
{context}"""

# Default age group when not provided
_DEFAULT_AGE_GROUP = "3-8"


def get_system_prompt(context: str, age_group: str = _DEFAULT_AGE_GROUP) -> str:
    """Build the system prompt with the given context and age group."""
    from app.core.config import settings
    return SYSTEM_PROMPT_TEMPLATE.format(
        name=settings.APP_NAME,
        age_group=age_group,
        context=context,
    )


# ---- Prompt manifest (metadata for all prompts) ----
# Schema per entry:
#   version: int — increment on breaking changes
#   active: bool — false = deprecated, loader should warn
#   category: str — matches directory name
#   description: str — what this prompt is for
#   expected_variables: list[str] — template variables that must be provided
#   output_format: str — what the AI should return
#   language_flexible: bool — true if this prompt should adapt to user's language
#   tone: str — expected tone (always "warm_encouraging" for child platform)
#   max_tokens_recommended: int — recommended max_tokens for this prompt

_PROMPT_METADATA: dict[str, dict] = {
    "system/default": {
        "version": 2,
        "active": True,
        "category": "system",
        "description": "Default system prompt injected before every AI call",
        "expected_variables": ["context", "age_group"],
        "output_format": "free-form creative text",
        "language_flexible": True,
        "tone": "warm_encouraging",
        "max_tokens_recommended": 1024,
    },
    "stories/create": {
        "version": 2,
        "active": True,
        "category": "stories",
        "description": "Generate a personalized story for a child",
        "expected_variables": ["age", "theme", "child_name", "setting", "word_count"],
        "output_format": "short story, 3-5 paragraphs, positive ending",
        "language_flexible": True,
        "tone": "warm_encouraging",
        "max_tokens_recommended": 1024,
    },
    "activities/create": {
        "version": 1,
        "active": True,
        "category": "activities",
        "description": "Generate a hands-on activity from a theme",
        "expected_variables": ["age", "activity_type", "duration", "materials"],
        "output_format": "structured: Title, Materials, Instructions, Challenge Question",
        "language_flexible": True,
        "tone": "warm_encouraging",
        "max_tokens_recommended": 1024,
    },
    "activities/generate": {
        "version": 2,
        "active": True,
        "category": "activities",
        "description": "Generate a hands-on activity from a story",
        "expected_variables": ["age_group", "story_text", "activity_mode"],
        "output_format": "structured: Title, Materials, Instructions, Challenge Question",
        "language_flexible": True,
        "tone": "warm_encouraging",
        "max_tokens_recommended": 1024,
    },
    "reflections/image": {
        "version": 2,
        "active": True,
        "category": "reflections",
        "description": "Generate a positive reflection on a child's artwork/image",
        "expected_variables": [],
        "output_format": "encouraging paragraph followed by 'Challenge Question:'",
        "language_flexible": True,
        "tone": "warm_encouraging",
        "max_tokens_recommended": 512,
    },
}

# Path for JSON manifest (checked at runtime, but metadata is source-of-truth)
_MANIFEST_PATH = PROMPT_DIR / "prompts.json"


def get_prompt_metadata(prompt_key: str) -> dict | None:
    """Get metadata for a prompt template by its key (e.g. 'stories/create')."""
    return _PROMPT_METADATA.get(prompt_key)


def get_all_metadata() -> dict:
    """Get all prompt metadata."""
    return dict(_PROMPT_METADATA)


def is_prompt_active(prompt_key: str) -> bool:
    """Check if a prompt template is active (not deprecated)."""
    meta = get_prompt_metadata(prompt_key)
    if meta is None:
        return False
    return meta.get("active", True)


def get_prompt_version(prompt_key: str) -> int:
    """Get the version number of a prompt template."""
    meta = get_prompt_metadata(prompt_key)
    if meta is None:
        return 0
    return meta.get("version", 0)


def export_manifest() -> dict:
    """Export the full manifest as a JSON-serializable dict.

    This can be written to prompts.json and served via API later.
    """
    return {
        "version": 2,
        "generated_at": None,  # filled at write time
        "prompts": _PROMPT_METADATA,
    }


def write_manifest() -> None:
    """Write the prompt manifest to prompts.json for external inspection."""
    from datetime import datetime, timezone

    manifest = export_manifest()
    manifest["generated_at"] = datetime.now(timezone.utc).isoformat()
    _MANIFEST_PATH.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info("Prompt manifest written", extra={"path": str(_MANIFEST_PATH)})