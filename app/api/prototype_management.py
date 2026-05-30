"""Prototype Management API — master CRUD, status tracking, photos, notes, materials, cost sheets, build records."""

import json
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from pydantic import BaseModel, Field
from sqlmodel import Session, select
from starlette import status

from app.db.session import get_session
from app.models.prototype_master import PrototypeMaster

router = APIRouter(prefix="/api/v1/prototypes", tags=["prototype-management"])

# Photo storage
PHOTO_DIR = Path(__file__).resolve().parent.parent.parent / "uploads" / "prototype-photos"
VALID_STATUSES = {"PLANNED", "MATERIAL_PENDING", "IN_PROGRESS", "COMPLETED", "FAILED", "NEEDS_REVISION"}


# --- Pydantic Schemas ---

class CreatePrototypeRequest(BaseModel):
    project_id: str = Field(default="", description="Reference to the science project")
    name: str = Field(..., description="Prototype name", examples=["Hydraulic Bridge V1"])
    description: str = Field(default="", description="Description of the prototype")
    assigned_to: str = Field(default="", description="Who is building this")


class UpdateStatusRequest(BaseModel):
    status: str = Field(..., description="New status", examples=["IN_PROGRESS"])


class AddNoteRequest(BaseModel):
    note: str = Field(..., description="Note content", examples=["Cardboard bends under weight"])


class AddMaterialRequest(BaseModel):
    material: str = Field(..., description="Material name", examples=["Cardboard"])
    quantity: float = Field(default=1, description="Quantity")
    unit: str = Field(default="piece", description="Unit", examples=["sheet", "meter", "piece"])


class AddCostSheetRequest(BaseModel):
    items: list[dict] = Field(default_factory=list, description="Cost items (name, cost)")
    total_estimated_cost_rs: float = Field(default=0)
    total_actual_cost_rs: float = Field(default=0)


class AddBuildRecordRequest(BaseModel):
    hours_spent: float = Field(default=0, description="Hours spent building")
    travel_cost: float = Field(default=0, description="Travel expenses")
    build_date: str = Field(default="", description="Date of build", examples=["2026-05-30"])


class PrototypeResponse(BaseModel):
    id: int
    project_id: str
    name: str
    description: str
    status: str
    assigned_to: str
    total_cost_rs: float
    created_at: datetime
    updated_at: datetime


# --- Helper ---

def _ensure_photo_dir():
    PHOTO_DIR.mkdir(parents=True, exist_ok=True)


# --- CRUD Endpoints ---

@router.post("", response_model=PrototypeResponse, status_code=status.HTTP_201_CREATED, summary="Create prototype")
async def create_prototype(body: CreatePrototypeRequest, session: Session = Depends(get_session)):
    """Create a new prototype record."""
    proto = PrototypeMaster(
        project_id=body.project_id,
        name=body.name,
        description=body.description,
        assigned_to=body.assigned_to,
    )
    session.add(proto)
    session.commit()
    session.refresh(proto)
    return proto


@router.get("", response_model=list[PrototypeResponse], summary="List prototypes")
async def list_prototypes(
    status_filter: str = Query(default="", alias="status"),
    project_id: str = Query(default="", alias="project_id"),
    assigned_to: str = Query(default="", alias="assigned_to"),
    session: Session = Depends(get_session),
):
    """List prototypes with optional filters."""
    query = select(PrototypeMaster).where(PrototypeMaster.is_active == True)
    if status_filter:
        query = query.where(PrototypeMaster.status == status_filter.upper())
    if project_id:
        query = query.where(PrototypeMaster.project_id == project_id)
    if assigned_to:
        query = query.where(PrototypeMaster.assigned_to == assigned_to)
    query = query.order_by(PrototypeMaster.created_at.desc())
    return session.exec(query).all()


@router.get("/{prototype_id}", response_model=PrototypeResponse, summary="Get prototype by ID")
async def get_prototype(prototype_id: int, session: Session = Depends(get_session)):
    """Get a single prototype by ID."""
    proto = session.get(PrototypeMaster, prototype_id)
    if not proto:
        raise HTTPException(status_code=404, detail="Prototype not found")
    return proto


# --- Status ---

@router.put("/{prototype_id}/status", response_model=PrototypeResponse, summary="Update prototype status")
async def update_status(prototype_id: int, body: UpdateStatusRequest, session: Session = Depends(get_session)):
    """Update the status of a prototype."""
    if body.status.upper() not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(sorted(VALID_STATUSES))}")
    proto = session.get(PrototypeMaster, prototype_id)
    if not proto:
        raise HTTPException(status_code=404, detail="Prototype not found")
    proto.status = body.status.upper()
    proto.updated_at = datetime.utcnow()
    session.add(proto)
    session.commit()
    session.refresh(proto)
    return proto


# --- Photos ---

@router.post("/{prototype_id}/photos", status_code=status.HTTP_201_CREATED, summary="Upload prototype photo")
async def upload_photo(prototype_id: int, file: UploadFile = File(...), session: Session = Depends(get_session)):
    """Upload a photo for a prototype."""
    proto = session.get(PrototypeMaster, prototype_id)
    if not proto:
        raise HTTPException(status_code=404, detail="Prototype not found")
    _ensure_photo_dir()
    filename = f"proto_{prototype_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    filepath = PHOTO_DIR / filename
    content = await file.read()
    filepath.write_bytes(content)
    return {"status": "ok", "filename": filename, "size_bytes": len(content), "prototype_id": prototype_id}


@router.get("/{prototype_id}/photos", summary="List prototype photos")
async def list_photos(prototype_id: int, session: Session = Depends(get_session)):
    """List all photos for a prototype."""
    proto = session.get(PrototypeMaster, prototype_id)
    if not proto:
        raise HTTPException(status_code=404, detail="Prototype not found")
    _ensure_photo_dir()
    photos = sorted(PHOTO_DIR.glob(f"proto_{prototype_id}_*"))
    return {
        "prototype_id": prototype_id,
        "photos": [{"filename": p.name, "path": str(p), "size_bytes": p.stat().st_size} for p in photos],
        "count": len(photos),
    }


# --- Notes ---

@router.post("/{prototype_id}/notes", summary="Add prototype note")
async def add_note(prototype_id: int, body: AddNoteRequest, session: Session = Depends(get_session)):
    """Add a text note about a prototype build."""
    proto = session.get(PrototypeMaster, prototype_id)
    if not proto:
        raise HTTPException(status_code=404, detail="Prototype not found")
    notes = json.loads(proto.notes) if proto.notes else []
    note_entry = {
        "id": str(uuid.uuid4()),
        "note": body.note,
        "created_at": datetime.utcnow().isoformat(),
    }
    notes.append(note_entry)
    proto.notes = json.dumps(notes, default=str)
    proto.updated_at = datetime.utcnow()
    session.add(proto)
    session.commit()
    return {"status": "ok", "note_id": note_entry["id"], "note": body.note}


@router.get("/{prototype_id}/notes", summary="Get prototype notes")
async def get_notes(prototype_id: int, session: Session = Depends(get_session)):
    """Get all notes for a prototype."""
    proto = session.get(PrototypeMaster, prototype_id)
    if not proto:
        raise HTTPException(status_code=404, detail="Prototype not found")
    notes = json.loads(proto.notes) if proto.notes else []
    return {"prototype_id": prototype_id, "notes": notes, "count": len(notes)}


# --- Materials ---

@router.post("/{prototype_id}/materials", summary="Add prototype material")
async def add_material(prototype_id: int, body: AddMaterialRequest, session: Session = Depends(get_session)):
    """Add a material entry for a prototype."""
    proto = session.get(PrototypeMaster, prototype_id)
    if not proto:
        raise HTTPException(status_code=404, detail="Prototype not found")
    materials = json.loads(proto.materials) if proto.materials else []
    material_entry = {
        "id": str(uuid.uuid4()),
        "material": body.material,
        "quantity": body.quantity,
        "unit": body.unit,
        "created_at": datetime.utcnow().isoformat(),
    }
    materials.append(material_entry)
    proto.materials = json.dumps(materials, default=str)
    proto.updated_at = datetime.utcnow()
    session.add(proto)
    session.commit()
    return {"status": "ok", "material_id": material_entry["id"], "material": body.material}


@router.get("/{prototype_id}/materials", summary="Get prototype materials")
async def get_materials(prototype_id: int, session: Session = Depends(get_session)):
    """Get all materials for a prototype."""
    proto = session.get(PrototypeMaster, prototype_id)
    if not proto:
        raise HTTPException(status_code=404, detail="Prototype not found")
    materials = json.loads(proto.materials) if proto.materials else []
    return {"prototype_id": prototype_id, "materials": materials, "count": len(materials)}


# --- Cost Sheets ---

@router.post("/{prototype_id}/cost-sheets", summary="Create prototype cost sheet")
async def create_cost_sheet(prototype_id: int, body: AddCostSheetRequest, session: Session = Depends(get_session)):
    """Create a cost sheet entry for a prototype."""
    proto = session.get(PrototypeMaster, prototype_id)
    if not proto:
        raise HTTPException(status_code=404, detail="Prototype not found")
    sheets = json.loads(proto.cost_sheets) if proto.cost_sheets else []
    sheet_entry = {
        "id": str(uuid.uuid4()),
        "items": body.items,
        "total_estimated_cost_rs": body.total_estimated_cost_rs,
        "total_actual_cost_rs": body.total_actual_cost_rs,
        "created_at": datetime.utcnow().isoformat(),
    }
    sheets.append(sheet_entry)
    proto.cost_sheets = json.dumps(sheets, default=str)
    proto.total_cost_rs = sum(s.get("total_actual_cost_rs", 0) for s in sheets)
    proto.updated_at = datetime.utcnow()
    session.add(proto)
    session.commit()
    return {"status": "ok", "cost_sheet_id": sheet_entry["id"]}


@router.get("/{prototype_id}/cost-sheets", summary="Get prototype cost sheets")
async def get_cost_sheets(prototype_id: int, session: Session = Depends(get_session)):
    """Get all cost sheets for a prototype."""
    proto = session.get(PrototypeMaster, prototype_id)
    if not proto:
        raise HTTPException(status_code=404, detail="Prototype not found")
    sheets = json.loads(proto.cost_sheets) if proto.cost_sheets else []
    return {"prototype_id": prototype_id, "cost_sheets": sheets, "count": len(sheets), "total_cost_rs": proto.total_cost_rs}


# --- Build Records ---

@router.post("/{prototype_id}/build-records", summary="Create prototype build record")
async def create_build_record(prototype_id: int, body: AddBuildRecordRequest, session: Session = Depends(get_session)):
    """Create a build record for a prototype."""
    proto = session.get(PrototypeMaster, prototype_id)
    if not proto:
        raise HTTPException(status_code=404, detail="Prototype not found")
    records = json.loads(proto.build_records) if proto.build_records else []
    record_entry = {
        "id": str(uuid.uuid4()),
        "hours_spent": body.hours_spent,
        "travel_cost": body.travel_cost,
        "build_date": body.build_date,
        "created_at": datetime.utcnow().isoformat(),
    }
    records.append(record_entry)
    proto.build_records = json.dumps(records, default=str)
    proto.updated_at = datetime.utcnow()
    session.add(proto)
    session.commit()
    return {"status": "ok", "build_record_id": record_entry["id"]}


@router.get("/{prototype_id}/build-records", summary="Get prototype build records")
async def get_build_records(prototype_id: int, session: Session = Depends(get_session)):
    """Get all build records for a prototype."""
    proto = session.get(PrototypeMaster, prototype_id)
    if not proto:
        raise HTTPException(status_code=404, detail="Prototype not found")
    records = json.loads(proto.build_records) if proto.build_records else []
    return {"prototype_id": prototype_id, "build_records": records, "count": len(records)}