from pydantic import BaseModel
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

    class Config:
        orm_mode = True