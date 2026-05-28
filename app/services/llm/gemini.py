"""Gemini provider implementation via Google AI API."""

import google.generativeai as genai

from app.services.llm.base import BaseLLMProvider, LLMResponse
from app.utils.logger import get_logger

logger = get_logger("app.llm.gemini")


class GeminiProvider(BaseLLMProvider):
    """Google Gemini LLM provider."""

    def __init__(
        self,
        api_key: str = "",
        model: str = "gemini-2.0-flash-001",
    ) -> None:
        self._api_key = api_key
        self._default_model = model
        self._model_instance = None

    def _get_model(self):
        if self._model_instance is None:
            genai.configure(api_key=self._api_key)
            self._model_instance = genai.GenerativeModel(self._default_model)
        return self._model_instance

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        image_url: str | None = None,
    ) -> LLMResponse:
        model = self._get_model()

        try:
            response = await model.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                ),
            )
            content = response.text or ""
            usage = {
                "prompt_tokens": getattr(response, "usage_metadata", {}).get("prompt_token_count", 0) if hasattr(response, "usage_metadata") else 0,
                "completion_tokens": getattr(response, "usage_metadata", {}).get("candidates_token_count", 0) if hasattr(response, "usage_metadata") else 0,
                "total_tokens": getattr(response, "usage_metadata", {}).get("total_token_count", 0) if hasattr(response, "usage_metadata") else 0,
            }
            return LLMResponse(
                content=content,
                provider="gemini",
                model=self._default_model,
                usage=usage,
            )
        except Exception as e:
            logger.error("Gemini API call failed", extra={"error": str(e)})
            raise