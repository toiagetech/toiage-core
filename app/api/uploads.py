from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from sqlmodel import Session

from app.db.session import get_session
from app.models.upload import Upload
from app.prompts import load_prompt
from app.schemas.upload import ReflectionResponse, UploadResponse
from app.services.analytics import EVENT_REFLECTION_GENERATED, EVENT_UPLOAD_CREATED, analytics
from app.services.llm.manager import llm_manager
from app.services.uploads import save_upload

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("/image", response_model=UploadResponse, status_code=201)
async def upload_image(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    """Upload an image file and save metadata."""
    try:
        meta = save_upload(file)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    upload = Upload(
        filename=meta["filename"],
        original_name=meta["original_name"],
        file_size=meta["file_size"],
        mime_type=meta["mime_type"],
        url=meta["url"],
    )
    session.add(upload)
    session.commit()
    session.refresh(upload)
    analytics.track(
        EVENT_UPLOAD_CREATED,
        properties={
            "upload_id": upload.id,
            "file_size": upload.file_size,
            "mime_type": upload.mime_type,
        },
    )
    return upload


@router.post("/{upload_id}/reflect", response_model=ReflectionResponse)
async def reflect_on_upload(
    upload_id: int,
    request: Request,
    session: Session = Depends(get_session),
):
    """Generate a positive AI reflection for an uploaded child creation image."""
    upload = session.get(Upload, upload_id)
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    prompt = load_prompt("reflections", "image")

    # Build full image URL
    base_url = str(request.base_url).rstrip("/")
    image_url = f"{base_url}{upload.url}"

    result = await llm_manager.generate(
        prompt=prompt,
        temperature=0.7,
        max_tokens=512,
        image_url=image_url,
    )

    analytics.track(
        EVENT_REFLECTION_GENERATED,
        properties={
            "upload_id": upload.id,
            "mime_type": upload.mime_type,
        },
    )

    return ReflectionResponse(
        upload_id=upload.id,
        message=result.content,
        curiosity_question="",
    )