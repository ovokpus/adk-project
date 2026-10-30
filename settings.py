"""Shared runtime settings for the agents and the local console.

Credentials are never required at import time: every agent can be imported, inspected
and tested offline. Running an agent needs ONE of:
  * Gemini API:  GOOGLE_API_KEY=...            (GOOGLE_GENAI_USE_VERTEXAI unset/false)
  * Vertex AI / Agent Platform: GOOGLE_GENAI_USE_VERTEXAI=true (or GOOGLE_GENAI_USE_ENTERPRISE=true),
    GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION and Application Default Credentials.
"""

import os

from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = "gemini-3.5-flash"  # the model the original lab specifies
MODEL = os.getenv("MODEL") or DEFAULT_MODEL
ENABLE_CLOUD_LOGGING = os.getenv("ENABLE_CLOUD_LOGGING", "false").lower() in {"1", "true", "yes"}


def _truthy(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes"}


def llm_status() -> dict:
    """Which backend would serve model calls, and if none, why. Never returns secret values."""
    if _truthy("GOOGLE_GENAI_USE_VERTEXAI") or _truthy("GOOGLE_GENAI_USE_ENTERPRISE"):
        project = os.getenv("GOOGLE_CLOUD_PROJECT")
        if not project:
            return {"configured": False, "backend": "vertex",
                    "reason": "Vertex AI mode is on but GOOGLE_CLOUD_PROJECT is not set."}
        try:
            import google.auth

            google.auth.default()
        except Exception as e:  # noqa: BLE001
            return {"configured": False, "backend": "vertex",
                    "reason": f"No Application Default Credentials found ({type(e).__name__})."}
        return {"configured": True, "backend": "vertex", "project": project,
                "location": os.getenv("GOOGLE_CLOUD_LOCATION", "global"), "reason": None}
    if os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"):
        return {"configured": True, "backend": "gemini-api", "reason": None}
    return {"configured": False, "backend": None,
            "reason": "No model credentials: set GOOGLE_API_KEY (Gemini API) or enable Vertex AI with ADC."}
