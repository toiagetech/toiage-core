from app.utils.logger import get_logger
from app.services.llm.base import BaseLLMProvider, LLMResponse
from app.services.llm.mock import MockLLMProvider
from app.services.llm.openrouter import OpenRouterProvider

logger = get_logger("app.llm.manager")

PROVIDER_MAP: dict[str, type[BaseLLMProvider]] = {
    "mock": MockLLMProvider,
    "openrouter": OpenRouterProvider,
}


class LLMManager:
    """Manages LLM provider instances and delegates requests."""

    def __init__(self) -> None:
        self._providers: dict[str, BaseLLMProvider] = {}

    def _get_provider(self, provider_name: str) -> BaseLLMProvider:
        if provider_name not in self._providers:
            provider_cls = PROVIDER_MAP.get(provider_name)
            if not provider_cls:
                raise ValueError(f"Unknown LLM provider: {provider_name}")
            self._providers[provider_name] = provider_cls()
        return self._providers[provider_name]

    async def generate(
        self,
        prompt: str,
        provider: str = "mock",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        image_url: str | None = None,
    ) -> LLMResponse:
        llm = self._get_provider(provider)
        has_image = image_url is not None
        logger.info(
            "AI call",
            extra={
                "provider": provider,
                "model": getattr(llm, "_default_model", "unknown"),
                "has_image": has_image,
                "prompt_preview": prompt[:120],
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        result = await llm.generate(
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            image_url=image_url,
        )
        logger.info(
            "AI response",
            extra={
                "provider": result.provider,
                "model": result.model,
                "response_preview": result.content[:120],
                "usage": result.usage,
            },
        )
        return result


# Singleton instance for app-wide use
llm_manager = LLMManager()