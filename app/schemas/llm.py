from pydantic import BaseModel


class LLMGenerateRequest(BaseModel):
    prompt: str
    provider: str = "mock"
    temperature: float = 0.7
    max_tokens: int = 1024


class LLMGenerateResponse(BaseModel):
    response: str
    provider: str
    model: str


class LLMGenerateWithTemplateRequest(BaseModel):
    template_category: str
    template_name: str
    variables: dict = {}
    provider: str = "mock"
    temperature: float = 0.7
    max_tokens: int = 1024
