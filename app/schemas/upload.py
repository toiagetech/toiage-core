"""Schemas for /uploads endpoints."""

from datetime import datetime

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    """Metadata for an uploaded image."""
    id: int = Field(..., description="Unique upload identifier", examples=[1])
    filename: str = Field(..., description="UUID-based filename on disk", examples=["a1b2c3d4-e5f6-7890-abcd-ef1234567890.png"])
    original_name: str = Field(..., description="Original filename from upload", examples=["my_drawing.png"])
    file_size: int = Field(..., description="File size in bytes", examples=[8632])
    mime_type: str = Field(..., description="MIME type of the image", examples=["image/png", "image/jpeg"])
    url: str = Field(..., description="URL to access the uploaded image", examples=["/uploads/files/a1b2c3d4e5f6.png"])
    created_at: datetime = Field(..., description="When the upload was created")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": 1,
                    "filename": "a1b2c3d4e5f6.png",
                    "original_name": "my_drawing.png",
                    "file_size": 8632,
                    "mime_type": "image/png",
                    "url": "/uploads/files/a1b2c3d4e5f6.png",
                    "created_at": "2026-05-22T10:00:00Z",
                }
            ]
        },
    }


class ReflectionRequest(BaseModel):
    """Request to generate an AI reflection on an uploaded image."""
    provider: str = Field(default="mock", description="LLM provider for reflection: mock, openrouter, or deepseek", examples=["mock", "openrouter"])


class ReflectionResponse(BaseModel):
    """AI-generated reflection on a child's artwork."""
    upload_id: int = Field(..., description="ID of the upload being reflected on", examples=[1])
    message: str = Field(..., description="Warm, encouraging reflection message from the AI", examples=["What a wonderful and colorful creation! I love how you used so many bright colors..."])
    curiosity_question: str = Field(default="", description="Optional follow-up question to encourage creativity", examples=["What would you add to this picture if you could imagine anything?"])

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "upload_id": 1,
                    "message": "What a wonderful and colorful creation! I love how you used so many bright colors...",
                    "curiosity_question": "What would you add to this picture?",
                }
            ]
        },
    }