"""Parent profile model — the main app user who manages children."""

from datetime import datetime

from sqlmodel import Field, SQLModel


class Parent(SQLModel, table=True):
    """A parent user of the Toiage app.

    The parent is the primary account holder who registers via mobile number
    or email, and manages one or more child profiles.
    """

    __tablename__ = "parents"

    id: int | None = Field(default=None, primary_key=True)

    # ── Identity ────────────────────────────────────────────────────
    name: str = Field(nullable=False, description="Parent's full name")
    email: str | None = Field(default=None, index=True, unique=True, description="Email address (login identifier)")
    mobile_number: str | None = Field(default=None, index=True, unique=True, description="Mobile number with country code (login identifier)")

    # ── Profile details ─────────────────────────────────────────────
    preferred_language: str = Field(default="en", description="Preferred language code (e.g. en, hi)")
    avatar_url: str | None = Field(default=None, description="Profile picture URL")

    # ── Status ──────────────────────────────────────────────────────
    is_active: bool = Field(default=True, description="Whether the account is active")

    # ── Timestamps ──────────────────────────────────────────────────
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)