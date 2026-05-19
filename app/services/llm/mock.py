from app.services.llm.base import BaseLLMProvider, LLMResponse


MOCK_RESPONSES: dict[str, str] = {
    "default": "Hello little explorer!",
    "greeting": "Hello little explorer! Ready for an adventure?",
    "activity": (
        "Title: Treasure Hunt Collage\n\n"
        "Materials:\n- Old magazines or colored paper\n- Glue stick\n- Scissors (child-safe)\n- A cardboard sheet\n\n"
        "Instructions:\n"
        "1. Flip through magazines and cut out colorful pictures.\n"
        "2. Arrange the cutouts on the cardboard to create a treasure map scene.\n"
        "3. Glue each piece down securely.\n"
        "4. Let it dry and display your treasure collage.\n\n"
        "Challenge Question: What other treasures would you hide in your magical forest?"
    ),
    "story": "Once upon a time, in a land of imagination, a brave child discovered a magical world full of wonder and joy.",
    "joke": "Why did the programmer's child bring a flashlight to bed? Because they wanted to debug their dreams!",
    "encouraging": (
        "What a wonderful and colorful creation! I love how you used so many bright "
        "colors and shapes to bring your imagination to life.\n\n"
        "Challenge Question: What would you add to this picture if you could imagine anything in the world?"
    ),
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
        image_url: str | None = None,
    ) -> LLMResponse:
        # Simple keyword matching for varied mock responses
        # image_url is accepted but ignored in mock mode
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