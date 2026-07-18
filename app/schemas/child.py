"""Schemas for /children endpoints."""

from datetime import date, datetime

from pydantic import BaseModel, Field


class ChildCreate(BaseModel):
    """Request to create a new child profile."""
    parent_id: str = Field(..., alias="parentId", description="Owning parent's user ID", examples=["parent-001"])
    name: str = Field(..., description="Child's first name", examples=["Aria"])
    nick_name: str | None = Field(default=None, alias="nickName", description="Child's nickname", examples=["Aru"])
    date_of_birth: date | None = Field(default=None, alias="dateOfBirth", description="Date of birth (ISO date)", examples=["2021-05-18"])
    gender: str | None = Field(default=None, description="Gender", examples=["FEMALE", "male", "other"])
    preferred_language: str = Field(default="en", alias="preferredLanguage", description="Preferred language code", examples=["en"])
    school_name: str | None = Field(default=None, alias="schoolName", description="School name", examples=["Little Stars Preschool"])
    current_class: str | None = Field(default=None, alias="currentClass", description="Current class/grade", examples=["UKG"])
    board: str | None = Field(default=None, description="Education board", examples=["CBSE"])
    interests: list[str] | None = Field(default=None, description="Child's interests", examples=[["Animals", "Space", "Building"]])
    favourite_subjects: list[str] | None = Field(default=None, alias="favouriteSubjects", description="Favourite subjects", examples=[["Science", "Art"]])
    learning_style: str | None = Field(default=None, alias="learningStyle", description="Learning style", examples=["VISUAL", "kinesthetic"])
    existing_toys: list[str] | None = Field(default=None, alias="existingToys", description="Existing toys at home")
    household_materials: list[str] | None = Field(default=None, alias="householdMaterials", description="Available household materials")
    special_notes: str | None = Field(default=None, alias="specialNotes", description="Special notes about the child")

    model_config = {"populate_by_name": True}


class ChildUpdate(BaseModel):
    """Request to update an existing child profile (all fields optional)."""
    name: str | None = Field(default=None, description="Child's first name", examples=["Aarav"])
    nick_name: str | None = Field(default=None, alias="nickName", description="Child's nickname", examples=["Aaru"])
    date_of_birth: date | None = Field(default=None, alias="dateOfBirth", description="Date of birth (ISO date)", examples=["2020-03-15"])
    gender: str | None = Field(default=None, description="Gender", examples=["male"])
    school_name: str | None = Field(default=None, alias="schoolName", description="School name")
    current_class: str | None = Field(default=None, alias="currentClass", description="Current class/grade")
    board: str | None = Field(default=None, description="Education board")
    preferred_language: str | None = Field(default=None, alias="preferredLanguage", description="Preferred language code")
    learning_style: str | None = Field(default=None, alias="learningStyle", description="Learning style")
    interests: list[str] | None = Field(default=None, description="Child's interests")
    favourite_subjects: list[str] | None = Field(default=None, alias="favouriteSubjects", description="Favourite subjects")
    existing_toys: list[str] | None = Field(default=None, alias="existingToys", description="Existing toys at home")
    household_materials: list[str] | None = Field(default=None, alias="householdMaterials", description="Available household materials")
    special_notes: str | None = Field(default=None, alias="specialNotes", description="Special notes about the child")

    model_config = {"populate_by_name": True}


class ChildRead(BaseModel):
    """A saved child profile."""
    id: int = Field(..., description="Unique child identifier", examples=[1])
    parent_id: str = Field(..., alias="parentId", description="Owning parent's user ID", examples=["parent-001"])
    name: str = Field(..., description="Child's first name")
    nick_name: str | None = Field(default=None, alias="nickName", description="Child's nickname")
    date_of_birth: date | None = Field(default=None, alias="dateOfBirth", description="Date of birth")
    gender: str | None = Field(default=None, description="Gender")
    school_name: str | None = Field(default=None, alias="schoolName", description="School name")
    current_class: str | None = Field(default=None, alias="currentClass", description="Current class/grade")
    board: str | None = Field(default=None, description="Education board")
    preferred_language: str = Field(default="en", alias="preferredLanguage", description="Preferred language code")
    learning_style: str | None = Field(default=None, alias="learningStyle", description="Learning style")
    interests: list[str] | None = Field(default=None, description="Child's interests")
    favourite_subjects: list[str] | None = Field(default=None, alias="favouriteSubjects", description="Favourite subjects")
    existing_toys: list[str] | None = Field(default=None, alias="existingToys", description="Existing toys at home")
    household_materials: list[str] | None = Field(default=None, alias="householdMaterials", description="Available household materials")
    special_notes: str | None = Field(default=None, alias="specialNotes", description="Special notes")
    created_at: datetime = Field(..., alias="createdAt", description="When the profile was created")
    updated_at: datetime = Field(..., alias="updatedAt", description="When the profile was last updated")

    model_config = {"from_attributes": True, "populate_by_name": True}