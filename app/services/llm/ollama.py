"""Ollama provider implementation for local AI models."""

from app.services.llm.base import BaseLLMProvider, LLMResponse
from app.utils.logger import get_logger

logger = get_logger("app.llm.ollama")


class OllamaProvider(BaseLLMProvider):
    """Ollama local LLM provider."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3.2",
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._default_model = model

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        image_url: str | None = None,
    ) -> LLMResponse:
        import httpx

        payload = {
            "model": self._default_model,
            "prompt": prompt,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
            "stream": False,
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(f"{self._base_url}/api/generate", json=payload)
                response.raise_for_status()
                data = response.json()

            content = data.get("response", "")
            usage = {
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
                "total_tokens": (data.get("prompt_eval_count", 0) or 0) + (data.get("eval_count", 0) or 0),
            }
            return LLMResponse(
                content=content,
                provider="ollama",
                model=self._default_model,
                usage=usage,
            )
        except Exception as e:
            logger.error("Ollama API call failed", extra={"error": str(e)})
            raise