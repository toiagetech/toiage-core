"""Schemas for science project generation endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class ScienceProjectGenerateRequest(BaseModel):
    """Request to generate a science project."""
    grade: int = Field(..., description="CBSE class grade (6, 7, or 8)", examples=[6])
    subject: str = Field(..., description="Subject name", examples=["Science", "Physics", "Chemistry", "Biology"])
    topic: str = Field(..., description="Topic for the project", examples=["Water Conservation", "Solar Energy"])
    difficulty: str = Field(default="medium", description="Difficulty level: easy, medium, or hard", examples=["medium"])
    budget: str = Field(default="low", description="Budget constraint: low, medium, or high", examples=["low"])
    provider: str = Field(default="mock", description="LLM provider: mock, openrouter, or deepseek", examples=["mock"])


class LearningObjective(BaseModel):
    """A single learning objective for a project."""
    objective: str = Field(..., description="Learning objective description")


class MaterialItem(BaseModel):
    """A single material item for a project."""
    item: str = Field(..., description="Name of the item")
    quantity: str = Field(..., description="Quantity needed", examples=["2"])
    unit: str = Field(..., description="Unit of measurement", examples=["pieces", "meters", "liters"])
    estimated_cost_rs: float = Field(..., description="Estimated cost in rupees", examples=[50])
    source: str = Field(..., description="Where to source the item", examples=["Kitchen", "Stationery shop"])
    notes: str | None = Field(default=None, description="Optional notes about the item")


class BuildStep(BaseModel):
    """A single build step for a project."""
    step_number: int = Field(..., description="Step number", examples=[1])
    title: str = Field(..., description="Step title")
    description: str = Field(..., description="Detailed step description")
    estimated_time_minutes: int = Field(..., description="Estimated time for this step", examples=[15])
    materials_needed: list[str] = Field(default_factory=list, description="Materials needed for this step")
    safety_note: str | None = Field(default=None, description="Safety precaution for this step")


class ScienceProjectResponse(BaseModel):
    """A generated science project with full details."""
    project_title: str = Field(..., description="Title of the project")
    subject: str = Field(..., description="Subject name")
    grade: int = Field(..., description="CBSE class grade", examples=[6])
    topic: str = Field(..., description="Topic covered")
    difficulty: str = Field(..., description="Difficulty level")
    estimated_build_time: str = Field(..., description="Estimated time to complete", examples=["2-3 hours"])
    estimated_cost: str = Field(..., description="Estimated cost range", examples=["₹150-₹300"])
    short_description: str = Field(..., description="Brief summary of the project")
    learning_objectives: list[str] = Field(default_factory=list, description="Learning objectives")
    curriculum_alignment: str = Field(..., description="CBSE curriculum alignment")
    materials: list[MaterialItem] = Field(default_factory=list, description="Materials needed")
    total_estimated_cost_rs: float = Field(default=0, description="Total estimated cost in rupees")
    safety_items_required: list[str] = Field(default_factory=list, description="Safety items needed")
    alternative_materials: list[str] = Field(default_factory=list, description="Alternative material options")
    total_steps: int = Field(default=0, description="Total number of build steps")
    steps: list[BuildStep] = Field(default_factory=list, description="Step-by-step build instructions")
    precautions: list[str] = Field(default_factory=list, description="Safety precautions")
    adult_supervision_required: bool = Field(default=True, description="Whether adult supervision is needed")
    tips_for_success: list[str] = Field(default_factory=list, description="Tips for successful completion")
    scientific_principle: str = Field(default="", description="Scientific principle demonstrated")
    simple_explanation: str = Field(default="", description="Age-appropriate explanation")
    how_project_demonstrates: str = Field(default="", description="How the project demonstrates the principle")
    real_world_applications: list[str] = Field(default_factory=list, description="Real-world applications")
    simple_analogy: str = Field(default="", description="Relatable analogy for the student")
    overall_difficulty: str = Field(default="medium", description="Overall difficulty assessment")
    provider: str = Field(default="mock", description="LLM provider used")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "project_title": "Working Model of Rainwater Harvesting",
                    "subject": "Science",
                    "grade": 6,
                    "topic": "Water Conservation",
                    "difficulty": "medium",
                    "estimated_build_time": "2-3 hours",
                    "estimated_cost": "₹150-₹300",
                    "short_description": "Build a working model demonstrating rainwater harvesting techniques.",
                    "learning_objectives": ["Understand water conservation", "Learn about rainwater harvesting"],
                    "curriculum_alignment": "CBSE Class 6 Science: Water",
                    "overall_difficulty": "medium",
                    "provider": "mock",
                }
            ]
        },
    }


class ScienceProjectGenerateResponse(BaseModel):
    """Response wrapper for science project generation."""
    project: ScienceProjectResponse = Field(..., description="The generated science project")
    project_id: int | None = Field(default=None, description="Database record ID", examples=[1])
    created_at: datetime | None = Field(default=None, description="When the project was created")
    prompt_tokens_used: int = Field(default=0, description="LLM prompt tokens used")
    completion_tokens_used: int = Field(default=0, description="LLM completion tokens used")
