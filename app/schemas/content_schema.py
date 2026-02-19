from pydantic import BaseModel, ConfigDict
from typing import Optional


class ContentCreate(BaseModel):
    title: str
    source: str


class ContentResponse(BaseModel):
    id: int
    title: str
    source: str
    summary: Optional[str]
    sentiment: Optional[str]

    model_config = ConfigDict(from_attributes=True)