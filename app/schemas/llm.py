"""Schemas for /ai/* endpoints."""

from pydantic import BaseModel, Field


class LLMGenerateRequest(BaseModel):
    """Request to send a raw prompt to an LLM provider."""
    prompt: str = Field(..., description="The prompt text to send to the LLM", examples=["Write a short story about a brave rabbit"])
    provider: str = Field(default="mock", description="LLM provider: mock, openrouter, or deepseek", examples=["mock", "openrouter"])
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature (0.0-2.0)", examples=[0.7, 1.0])
    max_tokens: int = Field(default=1024, ge=1, le=8192, description="Maximum tokens in the response", examples=[100, 1024])


class LLMGenerateResponse(BaseModel):
    """Response from an LLM provider."""
    response: str = Field(..., description="The generated text from the LLM", examples=["Once upon a time..."])
    provider: str = Field(..., description="The provider that generated the response", examples=["mock", "openrouter"])
    model: str = Field(..., description="The model that generated the response", examples=["mock-model-v1", "google/gemini-2.0-flash-001"])

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "response": "Hello little explorer!",
                    "provider": "mock",
                    "model": "mock-model-v1",
                }
            ]
        }
    }


class LLMGenerateWithTemplateRequest(BaseModel):
    """Request to load a prompt template, inject variables, and send to an LLM."""
    template_category: str = Field(..., description="Prompt category directory (e.g. stories, activities, reflections)", examples=["stories", "activities"])
    template_name: str = Field(..., description="Template filename without extension (e.g. create, generate, image)", examples=["create", "generate"])
    variables: dict = Field(default_factory=dict, description="Template variable values for {variable} substitution", examples=[{"age": "5", "theme": "friendship", "child_name": "Aria", "setting": "forest", "word_count": "100"}])
    provider: str = Field(default="mock", description="LLM provider: mock, openrouter, or deepseek", examples=["mock", "openrouter"])
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature (0.0-2.0)")
    max_tokens: int = Field(default=1024, ge=1, le=8192, description="Maximum tokens in the response")