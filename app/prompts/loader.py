from pathlib import Path


PROMPT_DIR = Path(__file__).parent


class PromptNotFoundError(FileNotFoundError):
    """Raised when a prompt template file is not found."""
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


def load_prompt(category: str, name: str, variables: dict | None = None) -> str:
    """Load a prompt template and inject variables.

    Args:
        category: Subdirectory under prompts/ (e.g. 'stories', 'activities', 'system').
        name: Template filename without extension (e.g. 'create', 'default').
        variables: Dict of variable names -> values for template substitution.

    Returns:
        Rendered prompt string.

    Raises:
        PromptNotFoundError: If the template file does not exist.
        KeyError: If a required template variable is missing from `variables`.
    """
    file_path = get_prompt_path(category, name)
    template = file_path.read_text(encoding="utf-8")

    if variables:
        template = template.format(**variables)

    return template