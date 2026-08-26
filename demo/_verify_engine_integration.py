import asyncio
import os
import sys

sys.path.insert(0, "/Users/manasmac/PARA/02-Area/codeWorkspace/wsMay2026/toiage-core")
os.environ["EDUCATION_ENGINE_URL"] = "http://127.0.0.1:8000"
os.environ["EDUCATION_ENGINE_API_VERSION"] = sys.argv[1] if len(sys.argv) > 1 else "v2"

from app.services.education_engine import generate_guidance  # noqa: E402

result = asyncio.run(generate_guidance({
    "question": "she cries when i am not giving her something she demanded",
    "child_profile": {"name": "pihu", "age": 3},
    "provider": "mock",
    "no_cache": True,
}))
print("MODE:", os.environ["EDUCATION_ENGINE_API_VERSION"])
print("status:", result.get("status"))
print("guidance chars:", len(result.get("guidance") or ""))
print("resources:", len(result.get("resources") or []))
print("keys:", sorted(result.keys())[:12])