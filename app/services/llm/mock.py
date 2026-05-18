from app.services.llm.base import BaseLLMProvider, LLMResponse


MOCK_RESPONSES: dict[str, str] = {
    "default": "Hello little explorer!",
    "greeting": "Hello little explorer! Ready for an adventure?",
    "story": "Once upon a time, in a land of imagination, a brave child discovered a magical world full of wonder and joy.",
    "joke": "Why did the programmer's child bring a flashlight to bed? Because they wanted to debug their dreams!",
}


class MockLLMProvider(BaseLLMProvider):
    """Mock provider for development and testing."""

    def __init__(self) -> None:
        self._provider_name = "mock"
        self._model_name = "mock-model-v1"

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        # Simple keyword matching for varied mock responses
        prompt_lower = prompt.lower()
        response_text = MOCK_RESPONSES["default"]

        for keyword, text in MOCK_RESPONSES.items():
            if keyword in prompt_lower:
                response_text = text
                break

        return LLMResponse(
            content=response_text,
            provider=self._provider_name,
            model=self._model_name,
            usage={"prompt_tokens": len(prompt.split()), "completion_tokens": len(response_text.split())},
        )