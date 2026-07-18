"""Child profile model — stores a parent's child profile for personalization."""

from datetime import date, datetime

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


class Child(SQLModel, table=True):
    """A child profile belonging to a parent.

    Used by the story/activity generation pipeline to personalize
    content (age, interests, learning style, etc.).
    """

    __tablename__ = "children"

    id: int | None = Field(default=None, primary_key=True)
    parent_id: str = Field(index=True, nullable=False, description="Owning parent's user ID")

    # ── Identity ────────────────────────────────────────────────────
    name: str = Field(nullable=False, description="Child's first name")
    nick_name: str | None = Field(default=None, description="Child's nickname")
    date_of_birth: date | None = Field(default=None, description="Date of birth (ISO date)")
    gender: str | None = Field(default=None, description="Gender (e.g. male, female, other)")

    # ── Education ───────────────────────────────────────────────────
    school_name: str | None = Field(default=None, description="School name")
    current_class: str | None = Field(default=None, description="Current class/grade (e.g. UKG, 1)")
    board: str | None = Field(default=None, description="Education board (e.g. CBSE, ICSE)")

    # ── Preferences ─────────────────────────────────────────────────
    preferred_language: str = Field(default="en", description="Preferred language code (e.g. en, hi)")
    learning_style: str | None = Field(default=None, description="Learning style (e.g. visual, kinesthetic)")

    # ── Arrays (stored as JSON) ─────────────────────────────────────
    interests: list | None = Field(default=None, sa_column=Column(JSON), description="Child's interests")
    favourite_subjects: list | None = Field(default=None, sa_column=Column(JSON), description="Favourite subjects")
    existing_toys: list | None = Field(default=None, sa_column=Column(JSON), description="Existing toys at home")
    household_materials: list | None = Field(default=None, sa_column=Column(JSON), description="Available household materials")

    # ── Notes ───────────────────────────────────────────────────────
    special_notes: str | None = Field(default=None, description="Special notes about the child")

    # ── Timestamps ──────────────────────────────────────────────────
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)