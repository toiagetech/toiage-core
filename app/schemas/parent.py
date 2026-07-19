"""Schemas for /parents endpoints."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, model_validator


class ParentCreate(BaseModel):
    """Request to create a parent profile (after registration)."""
    name: str = Field(..., description="Parent's full name", examples=["Manas Kumar"])
    email: EmailStr | None = Field(default=None, alias="email", description="Email address", examples=["manas@example.com"])
    mobile_number: str | None = Field(default=None, alias="mobileNumber", description="Mobile number with country code", examples=["+919876543210"])
    preferred_language: str = Field(default="en", alias="preferredLanguage", description="Preferred language code", examples=["en"])
    avatar_url: str | None = Field(default=None, alias="avatarUrl", description="Profile picture URL")

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def _require_email_or_mobile(self) -> "ParentCreate":
        """At least one of email or mobileNumber must be provided."""
        if not self.email and not self.mobile_number:
            raise ValueError("At least one of 'email' or 'mobileNumber' is required")
        return self


class ParentUpdate(BaseModel):
    """Request to update the current parent's profile (all fields optional)."""
    name: str | None = Field(default=None, description="Parent's full name")
    email: EmailStr | None = Field(default=None, description="Email address")
    mobile_number: str | None = Field(default=None, alias="mobileNumber", description="Mobile number with country code")
    preferred_language: str | None = Field(default=None, alias="preferredLanguage", description="Preferred language code")
    avatar_url: str | None = Field(default=None, alias="avatarUrl", description="Profile picture URL")

    model_config = {"populate_by_name": True}


class ParentRead(BaseModel):
    """A saved parent profile."""
    id: int = Field(..., description="Unique parent identifier", examples=[1])
    name: str = Field(..., description="Parent's full name")
    email: str | None = Field(default=None, description="Email address")
    mobile_number: str | None = Field(default=None, alias="mobileNumber", description="Mobile number with country code")
    preferred_language: str = Field(default="en", alias="preferredLanguage", description="Preferred language code")
    avatar_url: str | None = Field(default=None, alias="avatarUrl", description="Profile picture URL")
    is_active: bool = Field(default=True, alias="isActive", description="Whether the account is active")
    created_at: datetime = Field(..., alias="createdAt", description="When the profile was created")
    updated_at: datetime = Field(..., alias="updatedAt", description="When the profile was last updated")

    model_config = {"from_attributes": True, "populate_by_name": True}