"""Centralized orchestration layer for LLM workflows.

Handles model routing, context injection, retry logic, and response cleanup.
"""

import json
import re
from typing import Any

from app.prompts import load_prompt
from app.services.llm.manager import llm_manager
from app.utils.logger import get_logger

logger = get_logger("app.orchestration")


class Orchestrator:
    """Manages prompt execution with retries, routing, and response parsing."""

    def __init__(self) -> None:
        self.max_retries = 2

    async def execute_prompt(
        self,
        category: str,
        prompt_name: str,
        variables: dict[str, Any],
        provider: str = "mock",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        inject_system: bool = True,
        context: str = "",
        age_group: str = "",
    ) -> str:
        """Load, execute, and return raw LLM response for a prompt template."""
        prompt = load_prompt(
            category,
            prompt_name,
            variables,
            inject_system=inject_system,
            context=context or f"Generate using {category}/{prompt_name}",
            age_group=age_group,
        )

        result = await llm_manager.generate(
            prompt=prompt,
            provider=provider,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return result.content

    async def execute_with_retry(
        self,
        category: str,
        prompt_name: str,
        variables: dict[str, Any],
        provider: str = "mock",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        inject_system: bool = True,
        context: str = "",
        age_group: str = "",
    ) -> str:
        """Execute a prompt with automatic retry on failure."""
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                content = await self.execute_prompt(
                    category=category,
                    prompt_name=prompt_name,
                    variables=variables,
                    provider=provider,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    inject_system=inject_system,
                    context=context,
                    age_group=age_group,
                )

                if content.startswith("[") and "call failed" in content:
                    last_error = content
                    logger.warning(
                        "Orchestrator retry — LLM call failed",
                        extra={"attempt": attempt + 1, "category": category, "prompt": prompt_name},
                    )
                    continue

                return content
            except Exception as e:
                last_error = str(e)
                logger.warning(
                    "Orchestrator retry — exception",
                    extra={"attempt": attempt + 1, "error": str(e)},
                )

        logger.error(
            "Orchestrator — all retries exhausted",
            extra={"category": category, "prompt": prompt_name, "last_error": last_error},
        )
        return f"[Orchestration failed after {self.max_retries + 1} attempts]"

    def extract_json(self, raw_response: str) -> dict:
        """Extract and parse JSON from LLM response, handling markdown fences."""
        # Remove markdown code fences if present
        cleaned = re.sub(r"```(?:json)?\s*", "", raw_response).strip()
        # Try to find JSON object boundaries
        try:
            # Find first { and last }
            start = cleaned.index("{")
            end = cleaned.rindex("}")
            json_str = cleaned[start : end + 1]
            return json.loads(json_str)
        except (ValueError, json.JSONDecodeError) as e:
            logger.error(
                "Failed to parse JSON from LLM response",
                extra={"error": str(e), "response_preview": raw_response[:200]},
            )
            return {"error": "Failed to parse response", "raw": raw_response[:500]}

    def cleanup_response(self, raw_response: str, expected_fields: list[str] | None = None) -> dict:
        """Parse and validate LLM response against expected fields."""
        parsed = self.extract_json(raw_response)
        if "error" in parsed:
            return parsed

        if expected_fields:
            missing = [f for f in expected_fields if f not in parsed]
            if missing:
                logger.warning(
                    "Response missing expected fields",
                    extra={"missing_fields": missing, "present_fields": list(parsed.keys())},
                )

        return parsed


# Singleton instance
orchestrator = Orchestrator()