from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.models.content import Content, compute_content_hash
from app.services.content_formatter import normalize_content_fields


class WorkflowEngine:
    def __init__(self, summarizer_service, sentiment_service, vector_service=None):
        self.summarizer = summarizer_service
        self.sentiment = sentiment_service
        self.vector_service = vector_service

    def process_content(
        self,
        title: str,
        source: str,
        text: str,
        db: Session,
        url: Optional[str] = None,
        published_at: Optional[datetime] = None,
    ):
        # Step 1 - Duplicate check using content_hash and title
        content_hash = compute_content_hash(url=url, content=text, title=title)
        existing = db.query(Content).filter(
            (Content.content_hash == content_hash) | (Content.title == title)
        ).first()

        if existing:
            return {
                "message": "Article already processed",
                "title": title,
                "id": existing.id,
                "content_hash": existing.content_hash
            }

        # Step 2 - Process content with shared services
        clean_text = text if text else ""
        summary = self.summarizer.summarize(clean_text)
        sentiment_result = self.sentiment.analyze(summary or clean_text)
        sentiment_label = sentiment_result.get("label")

        # Step 3 - Normalize fields
        summary, sentiment_label = normalize_content_fields(summary, sentiment_label)

        # Step 4 - Save to database
        db_content = Content(
            title=title,
            source=source,
            content=clean_text,
            summary=summary,
            sentiment=sentiment_label,
            url=url,
            published_at=published_at,
            created_at=datetime.utcnow(),
            content_hash=content_hash,
        )

        db.add(db_content)
        db.commit()
        db.refresh(db_content)

        # Step 5 - Index into vector store if configured
        if self.vector_service is not None:
            try:
                self.vector_service.index_content(db_content)
            except Exception:
                pass

        return {
            "id": db_content.id,
            "title": title,
            "summary": summary,
            "sentiment": sentiment_label,
            "url": db_content.url,
            "content_hash": db_content.content_hash,
        }
