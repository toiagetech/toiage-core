import httpx

from app.core.config import settings
from app.services.llm.base import BaseLLMProvider, LLMResponse


class DeepSeekProvider(BaseLLMProvider):
    """DeepSeek LLM provider — OpenAI-compatible API."""

    def __init__(self) -> None:
        self._provider_name = "deepseek"
        self._base_url = settings.DEEPSEEK_BASE_URL.rstrip("/")
        self._api_key = settings.DEEPSEEK_API_KEY
        self._default_model = settings.DEEPSEEK_DEFAULT_MODEL
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
        image_url: str | None = None,
    ) -> LLMResponse:
        if not self._api_key:
            return LLMResponse(
                content="[DeepSeek not configured — set DEEPSEEK_API_KEY in .env]",
                provider=self._provider_name,
                model=self._default_model,
                usage={},
            )

        if image_url:
            content_parts = [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": image_url},
                },
            ]
            messages = [{"role": "user", "content": content_parts}]
        else:
            messages = [{"role": "user", "content": prompt}]

        payload = {
            "model": self._default_model,
            "messages": messages,
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
                content=f"[DeepSeek request timed out after {self._timeout}s]",
                provider=self._provider_name,
                model=self._default_model,
                usage={},
            )

        except httpx.HTTPStatusError as e:
            return LLMResponse(
                content=f"[DeepSeek API error: {e.response.status_code} - {e.response.text[:200]}]",
                provider=self._provider_name,
                model=self._default_model,
                usage={},
            )

        except Exception as e:
            return LLMResponse(
                content=f"[DeepSeek request failed: {type(e).__name__}: {e}]",
                provider=self._provider_name,
                model=self._default_model,
                usage={},
            )