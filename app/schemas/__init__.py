"""Shared Pydantic schemas for consistent API documentation."""

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standard error response returned on validation or server errors."""
    detail: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"detail": "Story not found"},
                {"detail": "Request body too large. Max: 1048576 bytes"},
                {"detail": "Unknown LLM provider: invalid"},
            ]
        }
    }


class ValidationErrorResponse(BaseModel):
    """Pydantic validation error response."""
    detail: list[dict]

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "detail": [
                        {
                            "loc": ["body", "prompt"],
                            "msg": "field required",
                            "type": "value_error.missing",
                        }
                    ]
                }
            ]
        }
    }