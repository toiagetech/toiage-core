"""Difficulty-level rules and configurations for educational content."""

from dataclasses import dataclass


@dataclass
class DifficultyRule:
    """Rules for a specific difficulty level."""
    name: str
    description: str
    typical_materials_count: tuple[int, int]  # (min, max)
    typical_project_steps: tuple[int, int]  # (min, max)
    typical_estimated_cost_rs: tuple[float, float]  # (min, max)
    adult_supervision: bool
    cognitive_levels: list[str]


DIFFICULTY_RULES: dict[str, DifficultyRule] = {
    "easy": DifficultyRule(
        name="easy",
        description="Simple projects with common household items, 3-5 steps",
        typical_materials_count=(3, 6),
        typical_project_steps=(3, 5),
        typical_estimated_cost_rs=(50, 200),
        adult_supervision=False,
        cognitive_levels=["recall", "understanding"],
    ),
    "medium": DifficultyRule(
        name="medium",
        description="Moderate projects requiring some specialty items, 5-8 steps",
        typical_materials_count=(5, 10),
        typical_project_steps=(5, 8),
        typical_estimated_cost_rs=(150, 500),
        adult_supervision=True,
        cognitive_levels=["understanding", "application"],
    ),
    "hard": DifficultyRule(
        name="hard",
        description="Complex projects requiring multiple materials and careful assembly, 8+ steps",
        typical_materials_count=(8, 15),
        typical_project_steps=(8, 15),
        typical_estimated_cost_rs=(300, 1000),
        adult_supervision=True,
        cognitive_levels=["application", "analysis", "evaluation"],
    ),
}


def get_difficulty_rule(difficulty: str) -> DifficultyRule | None:
    """Get the difficulty rule for a given level."""
    return DIFFICULTY_RULES.get(difficulty.lower())


def is_valid_difficulty(difficulty: str) -> bool:
    """Check if a difficulty level is valid."""
    return difficulty.lower() in DIFFICULTY_RULES