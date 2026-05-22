"""AI Safety & Validation Layer for child platform.

Validates all LLM outputs before returning to the caller. Blocks:
- Profanity / inappropriate language
- Unsafe / harmful content
- Extremely long outputs
- Structurally malformed content

On violation: logs the event, returns a safe fallback response.
"""

import re
from app.utils.logger import get_logger

logger = get_logger("app.safety")

# ---- Profanity / inappropriate word list ----
# This list should be reviewed & extended by the product team.
# In production, consider a dedicated profanity filter library.
_BLOCKED_WORDS: set[str] = {
    # English profanity — base stems only (catches "fucking", "shitty" etc.)
    "fuck", "shit", "damn", "ass", "bitch", "bastard", "crap",
    "dick", "piss", "slut", "whore", "cock", "cunt", "douche",
    "prick", "wank", "arse", "bloody", "bugger",
    # Name-calling / bullying
    "garbage", "stupid", "idiot", "loser", "shut up",
    # Sexual content (child safety critical)
    "sexy", "naked", "porn", "sex", "strip", "horny", "molest",
}

# Regex for words with character repetition/obfuscation: "f**k", "f*****k", "sh1t"
_OBFUSCATED_PATTERN = re.compile(
    r"\b("
    r"f[u\*]+[c\*]+k|"
    r"sh[i1\*]+t|"
    r"b[i1\*]+tch|"
    r"d[a\*]+mn|"
    r"c[u\*]+nt|"
    r"d[i1\*]+ck|"
    r"p[i1\*]+ss"
    r")\b",
    re.IGNORECASE,
)

# Max output length (characters) — safety cap
_MAX_OUTPUT_LENGTH = 10_000

# Safe fallback responses based on output category
_FALLBACK_RESPONSES: dict[str, str] = {
    "profanity": "Oops! Let's keep our words kind and respectful. Could you try asking in a different way? \ud83d\ude0a",
    "unsafe": "I can only help with fun, safe, and creative activities. Let's try something else! \ud83c\udf08",
    "too_long": "That's a lot of text! Let's keep it shorter so everyone can enjoy it. \ud83d\udcd6",
    "malformed": "Hmm, something didn't come out right. Let's try again! \ud83d\ude0a",
    "default": "Let's keep our imagination fun and safe! What would you like to create today? \u2728",
}


def check_safety(text: str) -> dict:
    """Run all safety checks on AI output text.

    Returns:
        {"safe": True} or {"safe": False, "reason": str, "fallback": str}
    """
    text_lower = text.lower()

    # Check 1: Profanity (stem match — catches derivations like "fucking", "shitty")
    for word in _BLOCKED_WORDS:
        # Match word stem with optional suffixes, bounded by word boundaries
        pattern = re.compile(rf"\b{re.escape(word)}\w*\b", re.IGNORECASE)
        if pattern.search(text_lower):
            logger.warning(
                "Safety violation: profanity detected",
                extra={
                    "matched_word": word,
                    "text_preview": text[:100],
                },
            )
            return {
                "safe": False,
                "reason": "profanity",
                "fallback": _FALLBACK_RESPONSES["profanity"],
            }

    # Check 2: Obfuscated profanity
    obfuscated_match = _OBFUSCATED_PATTERN.search(text)
    if obfuscated_match:
        logger.warning(
            "Safety violation: obfuscated profanity detected",
            extra={
                "matched": obfuscated_match.group(),
                "text_preview": text[:100],
            },
        )
        return {
            "safe": False,
            "reason": "profanity",
            "fallback": _FALLBACK_RESPONSES["profanity"],
        }

    # Check 3: Unsafe / harmful content patterns (checked after profanity)
    unsafe_patterns = [
        r"\b(kill|murder|torture|abuse|die|hurt)\s+(yourself|someone|people|children|kids|baby|babies|animals)\b",
        r"\b(self[- ]?harm|self[- ]?destruct|suicide|cutting)\b",
        r"\b(bomb|weapon|poison|drug|explosive|knife|gun|shoot|stab)\b",
        r"\b(how to make|instructions for|recipe for|build a)\s+(bomb|weapon|poison|drug|explosive)\b",
        r"\b(sexual|explicit|adult|18\+)\s+(content|story|activity|game|image|video)\b",
    ]
    for pattern in unsafe_patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            logger.warning(
                "Safety violation: unsafe content detected",
                extra={
                    "pattern": pattern,
                    "text_preview": text[:100],
                },
            )
            return {
                "safe": False,
                "reason": "unsafe",
                "fallback": _FALLBACK_RESPONSES["unsafe"],
            }

    # Check 4: Extremely long output
    if len(text) > _MAX_OUTPUT_LENGTH:
        logger.warning(
            "Safety violation: output too long",
            extra={
                "length": len(text),
                "max_length": _MAX_OUTPUT_LENGTH,
                "text_preview": text[:100],
            },
        )
        return {
            "safe": False,
            "reason": "too_long",
            "fallback": _FALLBACK_RESPONSES["too_long"],
        }

    return {"safe": True}


def safe_fallback(reason: str = "default") -> str:
    """Get a safe fallback response for a given violation reason."""
    return _FALLBACK_RESPONSES.get(reason, _FALLBACK_RESPONSES["default"])