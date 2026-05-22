from app.services.llm.base import BaseLLMProvider, LLMResponse

# Dynamic mock responses — pick based on prompt content
MOCK_RESPONSES: dict[str, str] = {
    "default": "Hello little explorer!",
    "greeting": "Hello little explorer! Ready for an adventure?",
    "joke": "Why did the programmer's child bring a flashlight to bed? Because they wanted to debug their dreams!",
    "encouraging": (
        "What a wonderful and colorful creation! I love how you used so many bright "
        "colors and shapes to bring your imagination to life.\n\n"
        "Challenge Question: What would you add to this picture if you could imagine anything in the world?"
    ),
}

# Dynamic story response — picks based on story theme
MOCK_STORY_RESPONSES: list[str] = [
    "Once upon a time, in a land of imagination, a brave child discovered a magical world full of wonder and joy.",
    "In a cozy little village, a curious puppy named Max found a mysterious golden key that opened a door to adventure.",
    "A little star named Twinkle fell from the sky and learned that even small lights can shine brightly.",
    "The rainbow fairy visited Lily's garden and turned every flower into a magical wishing bloom.",
    "Captain Bella sailed across the cotton-candy clouds to find the treasure of the giggles.",
]

# Dynamic activity responses — keyed by rough story theme keyword
MOCK_ACTIVITY_RESPONSES: list[dict[str, str]] = [
    {
        "title": "Magical Forest Diorama",
        "materials": "- A shoebox or small cardboard box\n- Colored paper (green, brown, blue)\n- Cotton balls\n- Child-safe glue and scissors\n- Small twigs or leaves from outside",
        "instructions": "1. Paint the inside of the shoebox blue for the sky and green for the ground.\n2. Cut tree shapes from brown and green paper and glue them inside.\n3. Glue cotton balls to the top for clouds.\n4. Place small twigs and leaves to create a forest floor.\n5. Let it dry and imagine your forest adventure!",
        "challenge": "What magical creature would you add to your forest and what would it do?",
    },
    {
        "title": "Rainbow Sensory Bottle",
        "materials": "- An empty clear plastic bottle with a cap\n- Water\n- Baby oil or vegetable oil\n- Liquid food coloring (red, yellow, blue)\n- Glitter (optional)\n- Strong glue to seal the cap",
        "instructions": "1. Fill the bottle halfway with water.\n2. Add several drops of food coloring and swirl gently.\n3. Fill the rest of the bottle with oil.\n4. Sprinkle in some glitter if you have it.\n5. Glue the cap on tightly and shake gently to watch the colors dance!",
        "challenge": "What other colors would you mix to make new ones in your bottle?",
    },
    {
        "title": "Paper Plate Puppet Theater",
        "materials": "- 2 paper plates per puppet\n- Crayons or markers\n- Craft sticks (popsicle sticks)\n- Glue or tape\n- Scissors (child-safe)\n- A large cardboard box for the stage",
        "instructions": "1. Decorate one paper plate with a face — this is your puppet's head.\n2. Glue or tape a craft stick to the back of the plate.\n3. Decorate the second plate as the body and glue it below the head.\n4. Cut and decorate the box to make a stage — cut a window in the front.\n5. Put on a puppet show for your family!",
        "challenge": "What story will your puppet tell, and what other characters would you make?",
    },
    {
        "title": "Nature Collage Treasure Map",
        "materials": "- A piece of cardboard or thick paper\n- Leaves, flowers, and small twigs collected from outside\n- Glue\n- Crayons or markers\n- Optional: small pebbles, grass, sand",
        "instructions": "1. Draw a map shape on your cardboard with a crayon.\n2. Glue leaves to mark forests and green areas.\n3. Use small pebbles to mark mountains or treasure spots.\n4. Draw a dashed path connecting the landmarks.\n5. Put an 'X' where the treasure is hidden!",
        "challenge": "What treasure would you hide at the end of your map, and who would find it?",
    },
    {
        "title": "Cardboard Castle Adventure",
        "materials": "- A large cardboard box\n- Tape and glue\n- Crayons, markers, or paint\n- Toilet paper rolls (for towers)\n- Construction paper (for flags and decorations)\n- Child-safe scissors",
        "instructions": "1. Cut the flaps off the box and tape them upright for castle walls.\n2. Tape toilet paper rolls to the corners as towers.\n3. Cut out a drawbridge shape on one side (fold, don't remove).\n4. Draw bricks, windows, and a castle door with markers.\n5. Make small flags from paper and stick them on the towers.",
        "challenge": "Who lives in your castle, and what friendly dragon would guard the gate?",
    },
]


class MockLLMProvider(BaseLLMProvider):
    """Mock provider for development and testing."""

    def __init__(self) -> None:
        self._provider_name = "mock"
        self._default_model = "mock-model-v1"

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        image_url: str | None = None,
    ) -> LLMResponse:
        prompt_lower = prompt.lower()
        response_text = MOCK_RESPONSES["default"]

        # Check order matters — activity check before generic "story" keyword
        import hashlib

        # Skip the system prompt boilderplate for keyword matching
        # Focus on the user-facing section after the "---" separator
        user_section = prompt_lower.split("---")[-1] if "---" in prompt_lower else prompt_lower

        # Activity generation (most specific first — prompt contains "story" text too)
        if "hands-on activity designer" in user_section:
            story_bytes = prompt.encode()
            idx = int(hashlib.md5(story_bytes).hexdigest(), 16) % len(MOCK_ACTIVITY_RESPONSES)
            act = MOCK_ACTIVITY_RESPONSES[idx]
            response_text = (
                f"Title: {act['title']}\n\n"
                f"Materials:\n{act['materials']}\n\n"
                f"Instructions:\n{act['instructions']}\n\n"
                f"Challenge Question: {act['challenge']}"
            )

        # Simple story request
        elif "write a short story" in user_section or ("/stories/create" in prompt_lower and "story" in user_section):
            story_bytes = prompt.encode()
            idx = int(hashlib.md5(story_bytes).hexdigest(), 16) % len(MOCK_STORY_RESPONSES)
            response_text = MOCK_STORY_RESPONSES[idx]

        # Simple keyword-based response selection (check user section only)
        else:
            for keyword, text in MOCK_RESPONSES.items():
                if keyword in prompt_lower and keyword not in ("encouraging", "default"):
                    response_text = text
                    break

        return LLMResponse(
            content=response_text,
            provider=self._provider_name,
            model=self._default_model,
            usage={"prompt_tokens": len(prompt.split()), "completion_tokens": len(response_text.split())},
        )