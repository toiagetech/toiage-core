"""AI LLM endpoints — test prompts and prompt templates."""

from fastapi import APIRouter, HTTPException
from starlette import status

from app.prompts import PromptNotFoundError, load_prompt
from app.schemas.llm import (
    LLMGenerateRequest,
    LLMGenerateResponse,
    LLMGenerateWithTemplateRequest,
)
from app.services.llm.manager import llm_manager

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post(
    "/test",
    response_model=LLMGenerateResponse,
    status_code=status.HTTP_200_OK,
    summary="Send raw prompt to LLM",
    description="Send a raw prompt string directly to any configured LLM provider (mock, openrouter, deepseek). Use this for testing provider responses without templates.",
    responses={
        400: {"description": "Invalid request (e.g., unknown provider)"},
    },
)
async def test_llm(body: LLMGenerateRequest):
    """Send a raw prompt directly to an LLM provider."""
    try:
        result = await llm_manager.generate(
            prompt=body.prompt,
            provider=body.provider,
            temperature=body.temperature,
            max_tokens=body.max_tokens,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return LLMGenerateResponse(
        response=result.content,
        provider=result.provider,
        model=result.model,
    )


@router.post(
    "/test-template",
    response_model=LLMGenerateResponse,
    status_code=status.HTTP_200_OK,
    summary="Load prompt template and send to LLM",
    description=(
        "Load a prompt template from the prompts/ directory, inject variables, "
        "prepend the system prompt (tone/safety rules), and send to an LLM provider. "
        "Use this to test prompt templates before integrating into business endpoints."
    ),
    responses={
        404: {"description": "Prompt template not found"},
        422: {"description": "Missing required template variable"},
        400: {"description": "Invalid request (e.g., unknown provider)"},
    },
)
async def test_llm_with_template(body: LLMGenerateWithTemplateRequest):
    """Load a prompt template, inject variables, and send to an LLM provider."""
    try:
        prompt = load_prompt(
            body.template_category,
            body.template_name,
            body.variables,
            inject_system=True,
            context=f"Generate a {body.template_category} template: {body.template_name}",
        )
    except PromptNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except KeyError as e:
        raise HTTPException(
            status_code=422, detail=f"Missing template variable: {e}"
        )

    try:
        result = await llm_manager.generate(
            prompt=prompt,
            provider=body.provider,
            temperature=body.temperature,
            max_tokens=body.max_tokens,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return LLMGenerateResponse(
        response=result.content,
        provider=result.provider,
        model=result.model,
    )