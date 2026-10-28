
from typing import Literal

from pydantic import BaseModel, Field


class DocumentParseResult(BaseModel):
    filename: str
    status: Literal["parsed"]
    content_type: str
    text: str
    character_count: int = Field(ge=0)
