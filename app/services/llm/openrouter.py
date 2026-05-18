import httpx

from app.core.config import settings
from app.services.llm.base import BaseLLMProvider, LLMResponse


class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter provider for real AI model access."""

    def __init__(self) -> None:
        self._provider_name = "openrouter"
        self._base_url = settings.OPENROUTER_BASE_URL
        self._api_key = settings.OPENROUTER_API_KEY
        self._default_model = settings.LLM_DEFAULT_MODEL
        self._timeout = settings.LLM_TIMEOUT_SECONDS
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=httpx.Timeout(self._timeout),
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
        )

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        if not self._api_key:
            return LLMResponse(
                content="[OpenRouter not configured — set OPENROUTER_API_KEY in .env]",
                provider=self._provider_name,
                model=self._default_model,
                usage={},
            )

        payload = {
            "model": self._default_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            response = await self._client.post("/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()

            choice = data["choices"][0]
            content = choice["message"]["content"]
            model_used = data.get("model", self._default_model)
            usage = data.get("usage", {})

            return LLMResponse(
                content=content,
                provider=self._provider_name,
                model=model_used,
                usage=usage,
            )

        except httpx.TimeoutException:
            return LLMResponse(
                content=f"[OpenRouter request timed out after {self._timeout}s]",
                provider=self._provider_name,
                model=self._default_model,
                usage={},
            )

        except httpx.HTTPStatusError as e:
            return LLMResponse(
                content=f"[OpenRouter API error: {e.response.status_code} - {e.response.text[:200]}]",
                provider=self._provider_name,
                model=self._default_model,
                usage={},
            )

        except Exception as e:
            return LLMResponse(
                content=f"[OpenRouter request failed: {type(e).__name__}: {e}]",
                provider=self._provider_name,
                model=self._default_model,
                usage={},
            )