import time
from contextvars import ContextVar

from app.services.llm.base import BaseLLMProvider, LLMResponse
from app.services.llm.deepseek import DeepSeekProvider
from app.services.llm.mock import MockLLMProvider
from app.services.llm.openrouter import OpenRouterProvider
from app.services.llm.response_cache import get_cached, set_cached
from app.utils.logger import get_logger
from app.utils.safety import check_safety

# Context variable for request_id — set by middleware, read anywhere in the call chain
request_id_var: ContextVar[str] = ContextVar("request_id", default="N/A")

logger = get_logger("app.llm.manager")

# Lazily imported providers (optional dependencies)
_LAZY_PROVIDERS: dict[str, str] = {
    "openai": "app.services.llm.openai.OpenAIProvider",
    "gemini": "app.services.llm.gemini.GeminiProvider",
    "ollama": "app.services.llm.ollama.OllamaProvider",
}

PROVIDER_MAP: dict[str, type[BaseLLMProvider]] = {
    "mock": MockLLMProvider,
    "openrouter": OpenRouterProvider,
    "deepseek": DeepSeekProvider,
}


def _latency_bucket(ms: float) -> str:
    if ms < 100:
        return "<100ms"
    elif ms < 300:
        return "<300ms"
    elif ms < 1000:
        return "<1s"
    elif ms < 3000:
        return "<3s"
    elif ms < 10000:
        return "<10s"
    else:
        return ">=10s"


class LLMManager:
    """Manages LLM provider instances and delegates requests with full observability."""

    def __init__(self) -> None:
        self._providers: dict[str, BaseLLMProvider] = {}
        self.total_calls = 0
        self.total_failures = 0

    def _get_provider(self, provider_name: str) -> BaseLLMProvider:
        if provider_name not in self._providers:
            provider_cls = PROVIDER_MAP.get(provider_name)
            if not provider_cls:
                # Try lazy import for optional providers
                lazy_path = _LAZY_PROVIDERS.get(provider_name)
                if lazy_path:
                    try:
                        import importlib
                        module_path, class_name = lazy_path.rsplit(".", 1)
                        module = importlib.import_module(module_path)
                        provider_cls = getattr(module, class_name)
                    except (ImportError, AttributeError, ModuleNotFoundError):
                        raise ValueError(
                            f"Provider '{provider_name}' not available. "
                            f"Install optional dependency or use a different provider. "
                            f"Available providers: {list(PROVIDER_MAP.keys())} + optional (openai, gemini, ollama)"
                        )
                else:
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
        rid = request_id_var.get()
        llm = self._get_provider(provider)
        has_image = image_url is not None
        start = time.monotonic()

        # --- Cache-aware mock: return cached OpenRouter response if available ---
        if provider == "mock":
            cached = get_cached(prompt, image_url)
            if cached:
                elapsed_ms = round((time.monotonic() - start) * 1000, 2)
                self.total_calls += 1
                logger.info(
                    "AI call (served from cache)",
                    extra={
                        "request_id": rid,
                        "provider": "mock",
                        "model": cached["model"],
                        "source": "cache",
                        "has_image": has_image,
                        "prompt_preview": prompt[:120],
                        "elapsed_ms": elapsed_ms,
                        "latency_bucket": _latency_bucket(elapsed_ms),
                    },
                )
                return LLMResponse(
                    content=cached["response"],
                    provider="mock",
                    model=f"cached:{cached['model']}",
                    usage={},
                )

        # --- Real AI call ---
        model = getattr(llm, "_default_model", "unknown")

        logger.info(
            "AI call",
            extra={
                "request_id": rid,
                "provider": provider,
                "model": model,
                "has_image": has_image,
                "prompt_preview": prompt[:120],
                "prompt_tokens": len(prompt.split()),
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )

        try:
            result = await llm.generate(
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                image_url=image_url,
            )
        except Exception as exc:
            elapsed_ms = round((time.monotonic() - start) * 1000, 2)
            self.total_calls += 1
            self.total_failures += 1
            logger.error(
                "AI call failed",
                extra={
                    "request_id": rid,
                    "provider": provider,
                    "model": model,
                    "elapsed_ms": elapsed_ms,
                    "latency_bucket": _latency_bucket(elapsed_ms),
                    "error": str(exc),
                },
                exc_info=True,
            )
            return LLMResponse(
                content=f"[{provider} call failed: {type(exc).__name__}]",
                provider=provider,
                model=model,
                usage={},
            )

        elapsed_ms = round((time.monotonic() - start) * 1000, 2)
        self.total_calls += 1

        # Detect failure from provider error responses
        input_tokens = result.usage.get("prompt_tokens", 0)
        output_tokens = result.usage.get("completion_tokens", 0)
        total_tokens = result.usage.get("total_tokens", 0)
        is_error = result.content.startswith("[") and "]" in result.content[:80]

        if is_error:
            self.total_failures += 1
            logger.error(
                "AI call failure (provider error)",
                extra={
                    "request_id": rid,
                    "provider": result.provider,
                    "model": result.model,
                    "elapsed_ms": elapsed_ms,
                    "latency_bucket": _latency_bucket(elapsed_ms),
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens,
                    "error": result.content[:120],
                },
            )
            return result

        # --- Safety check: validate output before returning ---
        safety = check_safety(result.content)
        if not safety["safe"]:
            self.total_failures += 1
            logger.warning(
                "AI response blocked by safety filter",
                extra={
                    "request_id": rid,
                    "provider": result.provider,
                    "model": result.model,
                    "reason": safety["reason"],
                    "response_preview": result.content[:80],
                },
            )
            # Replace content with safe fallback — structure stays intact
            result = LLMResponse(
                content=safety["fallback"],
                provider=result.provider,
                model=result.model,
                usage=result.usage,
            )

        # --- Cache OpenRouter responses (after safety check, block cache of unsafe) ---
        if provider == "openrouter":
            set_cached(prompt, result.content, result.provider, result.model, image_url)
            logger.info(
                "AI response (cached)",
                extra={
                    "request_id": rid,
                    "provider": result.provider,
                    "model": result.model,
                    "response_preview": result.content[:120],
                    "elapsed_ms": elapsed_ms,
                    "latency_bucket": _latency_bucket(elapsed_ms),
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens,
                    "usage": result.usage,
                },
            )
        else:
            logger.info(
                "AI response",
                extra={
                    "request_id": rid,
                    "provider": result.provider,
                    "model": result.model,
                    "response_preview": result.content[:120],
                    "elapsed_ms": elapsed_ms,
                    "latency_bucket": _latency_bucket(elapsed_ms),
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens,
                    "usage": result.usage,
                },
            )

        return result


# Singleton instance for app-wide use
llm_manager = LLMManager()