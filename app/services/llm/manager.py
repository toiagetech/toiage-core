from app.utils.logger import get_logger
from app.services.llm.base import BaseLLMProvider, LLMResponse
from app.services.llm.deepseek import DeepSeekProvider
from app.services.llm.mock import MockLLMProvider
from app.services.llm.openrouter import OpenRouterProvider
from app.services.llm.response_cache import get_cached, set_cached

logger = get_logger("app.llm.manager")

PROVIDER_MAP: dict[str, type[BaseLLMProvider]] = {
    "mock": MockLLMProvider,
    "openrouter": OpenRouterProvider,
    "deepseek": DeepSeekProvider,
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

        # --- Cache-aware mock: return cached OpenRouter response if available ---
        if provider == "mock":
            cached = get_cached(prompt, image_url)
            if cached:
                logger.info(
                    "AI call (served from cache)",
                    extra={
                        "provider": "mock",
                        "model": cached["model"],
                        "has_image": has_image,
                        "prompt_preview": prompt[:120],
                        "source": "cache",
                    },
                )
                return LLMResponse(
                    content=cached["response"],
                    provider="mock",
                    model=f"cached:{cached['model']}",
                    usage={},
                )

        # --- Real AI call ---
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

        # --- Cache OpenRouter responses for future mock credit savings ---
        if provider == "openrouter":
            set_cached(prompt, result.content, result.provider, result.model, image_url)
            logger.info(
                "AI response (cached)",
                extra={
                    "provider": result.provider,
                    "model": result.model,
                    "response_preview": result.content[:120],
                    "usage": result.usage,
                },
            )
        else:
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
