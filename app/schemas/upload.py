from datetime import datetime

from pydantic import BaseModel


class UploadResponse(BaseModel):
    id: int
    filename: str
    original_name: str
    file_size: int
    mime_type: str
    url: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ReflectionResponse(BaseModel):
    upload_id: int
    message: str
    curiosity_question: str