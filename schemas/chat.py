from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(description="用户问题")


class TokenUsage(BaseModel):
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)


class ChatResponse(BaseModel):
    answer: str
    usage: TokenUsage | None = None
    model: str
