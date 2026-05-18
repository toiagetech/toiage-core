from fastapi import APIRouter, HTTPException

from app.prompts import PromptNotFoundError, load_prompt
from app.schemas.llm import (
    LLMGenerateRequest,
    LLMGenerateResponse,
    LLMGenerateWithTemplateRequest,
)
from app.services.llm.manager import llm_manager

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/test", response_model=LLMGenerateResponse)
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


@router.post("/test-template", response_model=LLMGenerateResponse)
async def test_llm_with_template(body: LLMGenerateWithTemplateRequest):
    """Load a prompt template, inject variables, and send to an LLM provider."""
    try:
        prompt = load_prompt(body.template_category, body.template_name, body.variables)
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