"""Prototype documentation support APIs — store photos, notes, and build records."""

from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from pydantic import BaseModel, Field
from starlette import status

router = APIRouter(prefix="/api/v1/prototypes", tags=["prototype-docs"])

# Simple local file-based storage for prototype records
PROTOTYPE_STORAGE = Path(__file__).resolve().parent.parent.parent / "uploads" / "prototypes"


class PrototypeNote(BaseModel):
    """A note about a prototype build."""
    id: str = Field(..., description="Unique note identifier")
    prototype_id: str = Field(..., description="Prototype/project identifier")
    title: str = Field(..., description="Note title")
    content: str = Field(..., description="Note content")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class BuildRecord(BaseModel):
    """A record of a prototype build session."""
    id: str = Field(..., description="Unique record identifier")
    prototype_id: str = Field(..., description="Prototype/project identifier")
    build_date: str = Field(..., description="Date of build")
    materials_used: list[str] = Field(default_factory=list)
    actual_cost_rs: float = Field(default=0, description="Actual cost incurred")
    build_time_minutes: int = Field(default=0)
    challenges_faced: str = Field(default="")
    notes: str = Field(default="")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CostSheet(BaseModel):
    """A cost breakdown sheet for a prototype."""
    id: str = Field(..., description="Unique cost sheet identifier")
    prototype_id: str = Field(..., description="Prototype/project identifier")
    items: list[dict] = Field(default_factory=list)
    total_estimated_cost_rs: float = Field(default=0)
    total_actual_cost_rs: float = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)


def _ensure_storage():
    """Ensure the prototype storage directory exists."""
    PROTOTYPE_STORAGE.mkdir(parents=True, exist_ok=True)


@router.post("/{prototype_id}/photos", status_code=status.HTTP_201_CREATED, summary="Upload prototype photo")
async def upload_photo(prototype_id: str, file: UploadFile = File(...)):
    """Upload a photo of a prototype build."""
    _ensure_storage()
    prototype_dir = PROTOTYPE_STORAGE / prototype_id
    prototype_dir.mkdir(parents=True, exist_ok=True)

    file_path = prototype_dir / f"photo_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    content = await file.read()
    file_path.write_bytes(content)

    return {
        "status": "ok",
        "filename": file_path.name,
        "path": str(file_path),
        "size_bytes": len(content),
    }


@router.post("/{prototype_id}/notes", status_code=status.HTTP_201_CREATED, summary="Add prototype note")
async def add_note(prototype_id: str, title: str = Form(...), content: str = Form(...)):
    """Add a text note about a prototype build."""
    import uuid

    _ensure_storage()
    prototype_dir = PROTOTYPE_STORAGE / prototype_id
    prototype_dir.mkdir(parents=True, exist_ok=True)

    note = PrototypeNote(
        id=str(uuid.uuid4()),
        prototype_id=prototype_id,
        title=title,
        content=content,
    )

    notes_file = prototype_dir / "notes.json"
    existing = []
    if notes_file.exists():
        import json
        existing = json.loads(notes_file.read_text())

    existing.append(note.model_dump())
    notes_file.write_text(__import__("json").dumps(existing, indent=2, default=str))

    return {"status": "ok", "note_id": note.id}


@router.get("/{prototype_id}/records", summary="Get prototype build records")
async def get_records(prototype_id: str):
    """Get all build records and notes for a prototype."""
    _ensure_storage()
    prototype_dir = PROTOTYPE_STORAGE / prototype_id
    if not prototype_dir.exists():
        return {"prototype_id": prototype_id, "photos": [], "notes": [], "records": []}

    photos = sorted(prototype_dir.glob("photo_*"))
    notes = []
    notes_file = prototype_dir / "notes.json"
    if notes_file.exists():
        import json
        notes = json.loads(notes_file.read_text())

    return {
        "prototype_id": prototype_id,
        "photos": [p.name for p in photos],
        "notes": notes,
        "records": [],
    }


@router.post("/{prototype_id}/cost-sheet", status_code=status.HTTP_201_CREATED, summary="Create prototype cost sheet")
async def create_cost_sheet(prototype_id: str, cost_sheet: CostSheet):
    """Create a cost breakdown sheet for a prototype."""
    import uuid

    _ensure_storage()
    prototype_dir = PROTOTYPE_STORAGE / prototype_id
    prototype_dir.mkdir(parents=True, exist_ok=True)

    cost_sheet.id = str(uuid.uuid4())
    cost_sheet.prototype_id = prototype_id

    cost_file = prototype_dir / "cost_sheet.json"
    cost_file.write_text(__import__("json").dumps(cost_sheet.model_dump(), indent=2, default=str))

    return {"status": "ok", "cost_sheet_id": cost_sheet.id}