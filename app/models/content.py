import hashlib
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, DateTime
from app.models.database import Base


def compute_content_hash(
    url: Optional[str] = None,
    content: Optional[str] = None,
    title: Optional[str] = None
) -> str:
    """
    Generate SHA-256 hash from canonical URL, or normalized content / title.
    Used for duplicate detection.
    """
    if url and url.strip():
        raw_key = url.strip().lower()
    elif content and content.strip():
        raw_key = " ".join(content.strip().lower().split())
    elif title and title.strip():
        raw_key = " ".join(title.strip().lower().split())
    else:
        raw_key = ""
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


class Content(Base):
    __tablename__ = "contents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    sentiment = Column(String, nullable=True)
    source = Column(String, nullable=False)
    url = Column(String, nullable=True)
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=True)
    content_hash = Column(String, unique=True, index=True, nullable=True)