"""OpenAI provider implementation (compatible with OpenAI API)."""

from typing import Optional

from openai import AsyncOpenAI

from app.services.llm.base import BaseLLMProvider, LLMResponse
from app.utils.logger import get_logger

logger = get_logger("app.llm.openai")


class OpenAIProvider(BaseLLMProvider):
    """OpenAI-compatible LLM provider."""

    def __init__(
        self,
        api_key: str = "",
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini",
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url
        self._default_model = model
        self._client: AsyncOpenAI | None = None

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=self._api_key,
                base_url=self._base_url,
            )
        return self._client

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        image_url: str | None = None,
    ) -> LLMResponse:
        client = self._get_client()
        messages: list[dict] = [{"role": "user", "content": prompt}]

        kwargs = {
            "model": self._default_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            response = await client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content or ""
            usage = {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            }
            return LLMResponse(
                content=content,
                provider="openai",
                model=self._default_model,
                usage=usage,
            )
        except Exception as e:
            logger.error("OpenAI API call failed", extra={"error": str(e)})
            raise