from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger("app.analytics")

# Event names
EVENT_STORY_GENERATED = "story_generated"
EVENT_ACTIVITY_GENERATED = "activity_generated"
EVENT_UPLOAD_CREATED = "upload_created"
EVENT_REFLECTION_GENERATED = "reflection_generated"


class AnalyticsService:
    """Lightweight analytics service with PostHog integration placeholder."""

    def __init__(self) -> None:
        self._enabled = bool(settings.POSTHOG_API_KEY)
        self._client = None  # PostHog client would be initialized here

    def _init_client(self) -> None:
        """Lazy-init PostHog client (placeholder)."""
        if self._client or not self._enabled:
            return
        # PostHog integration:
        # import posthog
        # self._client = posthog.Posthog(
        #     settings.POSTHOG_API_KEY, host=settings.POSTHOG_HOST
        # )

    def track(
        self,
        event: str,
        distinct_id: str = "anonymous",
        properties: dict | None = None,
    ) -> None:
        """Track a product event."""
        if not self._enabled:
            # Log when PostHog is not configured
            logger.info(
                "Analytics event (not sent — POSTHOG_API_KEY not set)",
                extra={"event": event, "properties": properties or {}},
            )
            return

        self._init_client()
        # self._client.capture(distinct_id, event, properties or {})


# Singleton instance
analytics = AnalyticsService()