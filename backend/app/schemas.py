from typing import Optional
from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=128)
    message: str = Field(min_length=1, max_length=4000)
    system_prompt: Optional[str] = None

    @field_validator("session_id", "message")
    @classmethod
    def clean_text(cls, value):
        value = value.strip()

        if not value:
            raise ValueError("must not be empty")

        return value