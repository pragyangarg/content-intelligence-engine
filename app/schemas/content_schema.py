from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


class ContentCreate(BaseModel):
    title: str
    source: str
    content: Optional[str] = None
    url: Optional[str] = None
    published_at: Optional[datetime] = None


class ContentResponse(BaseModel):
    id: int
    title: str
    source: str
    content: Optional[str] = None
    summary: Optional[str] = None
    sentiment: Optional[str] = None
    url: Optional[str] = None
    published_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    content_hash: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SourceItem(BaseModel):
    title: str
    url: Optional[str] = None
    source: Optional[str] = None


class AskRequest(BaseModel):
    query: str


class AskResponse(BaseModel):
    answer: str
    sources: List[SourceItem] = []
    rewritten_query: Optional[str] = None


class SearchDocumentResponse(BaseModel):
    id: str
    article_id: Optional[int] = None
    title: str
    source: str
    url: Optional[str] = None
    published_at: Optional[str] = None
    content: str
    similarity: float
    distance: float