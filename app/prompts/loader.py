"""Prompt loader with metadata, system prompt injection, and version tracking."""

from pathlib import Path

from app.prompts.metadata import (
    get_prompt_metadata,
    get_system_prompt,
    is_prompt_active,
)
from app.utils.logger import get_logger

logger = get_logger("app.prompts")

PROMPT_DIR = Path(__file__).parent


class PromptNotFoundError(FileNotFoundError):
    """Raised when a prompt template file is not found."""
    pass


class PromptInactiveError(RuntimeError):
    """Raised when a prompt template is marked inactive/deprecated."""
    pass


class MissingVariableError(KeyError):
    """Raised when a required template variable is missing."""
    pass


def get_prompt_path(category: str, name: str) -> Path:
    """Resolve the full path for a prompt template.

    Args:
        category: Subdirectory under prompts/ (e.g. 'stories', 'activities', 'system').
        name: Template filename without extension (e.g. 'create', 'default').

    Returns:
        Path to the template file.

    Raises:
        PromptNotFoundError: If the template file does not exist.
    """
    file_path = PROMPT_DIR / category / f"{name}.txt"
    if not file_path.exists():
        raise PromptNotFoundError(
            f"Prompt template not found: {category}/{name}.txt "
            f"(searched in {PROMPT_DIR})"
        )
    return file_path


def load_prompt(
    category: str,
    name: str,
    variables: dict | None = None,
    *,
    inject_system: bool = True,
    context: str = "",
    age_group: str = "3-8",
) -> str:
    """Load a prompt template and inject variables.

    Optionally prepends the system prompt for tone/language/safety consistency.

    Args:
        category: Subdirectory under prompts/ (e.g. 'stories', 'activities', 'system').
        name: Template filename without extension (e.g. 'create', 'default').
        variables: Dict of variable names -> values for template substitution.
        inject_system: If True, prepend the system prompt before the category prompt.
        context: Context description for the system prompt.
        age_group: Age range for the system prompt (e.g. '3-5', '6-8').

    Returns:
        Rendered prompt string (with optional system prefix).

    Raises:
        PromptNotFoundError: If the template file does not exist.
        PromptInactiveError: If the prompt is marked inactive.
        MissingVariableError: If a required template variable is missing.
    """
    prompt_key = f"{category}/{name}"

    # Check metadata
    meta = get_prompt_metadata(prompt_key)
    if meta is None:
        logger.warning(
            "Unknown prompt template — no metadata found",
            extra={"prompt_key": prompt_key},
        )
    elif not meta.get("active", True):
        raise PromptInactiveError(
            f"Prompt template '{prompt_key}' is marked inactive/deprecated "
            f"(version {meta.get('version', '?')})"
        )
    else:
        # Log version for traceability
        logger.debug(
            "Loading prompt template",
            extra={
                "prompt_key": prompt_key,
                "version": meta.get("version"),
                "active": meta.get("active"),
                "category": meta.get("category"),
            },
        )

    # Load the template file
    file_path = get_prompt_path(category, name)
    template = file_path.read_text(encoding="utf-8")

    # Inject variables
    if variables:
        try:
            template = template.format(**variables)
        except KeyError as e:
            raise MissingVariableError(
                f"Missing template variable '{e.args[0]}' for prompt '{prompt_key}'"
            ) from e

    # Prepend system prompt for tone/safety/language consistency
    if inject_system and category != "system":
        sys_prompt = get_system_prompt(
            context=context or f"Generate a {category} template: {name}",
            age_group=age_group,
        )
        template = f"{sys_prompt}\n\n---\n\n{template}"

    return template