import json
import hashlib
from pathlib import Path

from app.core.config import settings

CACHE_DIR = Path(settings.UPLOAD_DIR).parent / ".llm_cache"
CACHE_FILE = CACHE_DIR / "responses.json"


def _prompt_key(prompt: str, image_url: str | None = None) -> str:
    """Generate a deterministic hash key for a prompt."""
    raw = prompt + (image_url or "")
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _load_cache() -> dict:
    """Load the entire response cache from disk."""
    if not CACHE_FILE.exists():
        return {}
    try:
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_cache(cache: dict) -> None:
    """Write the entire response cache to disk."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(cache, indent=2, default=str), encoding="utf-8")


def get_cached(prompt: str, image_url: str | None = None) -> dict | None:
    """Return cached response dict if it exists, else None."""
    key = _prompt_key(prompt, image_url)
    cache = _load_cache()
    entry = cache.get(key)
    if entry:
        return entry
    return None


def set_cached(
    prompt: str,
    response_text: str,
    provider: str,
    model: str,
    image_url: str | None = None,
) -> None:
    """Store an LLM response in the cache."""
    key = _prompt_key(prompt, image_url)
    cache = _load_cache()
    cache[key] = {
        "response": response_text,
        "provider": provider,
        "model": model,
        "image_url": image_url,
    }
    _save_cache(cache)