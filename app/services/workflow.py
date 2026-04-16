from sqlalchemy.orm import Session

from app.models.content import Content
from app.services.content_formatter import normalize_content_fields


class WorkflowEngine:
    def __init__(self, summarizer_service, sentiment_service):
        self.summarizer = summarizer_service
        self.sentiment = sentiment_service

    def process_content(self, title: str, source: str, text: str, db: Session):
        # Step 1 - Check duplicate
        existing = db.query(Content).filter(Content.title == title).first()

        if existing:
            return {
                "message": "Article already processed",
                "title": title
            }

        # Step 2 - Process content with shared services
        summary = self.summarizer.summarize(text)
        sentiment_result = self.sentiment.analyze(summary)
        sentiment_label = sentiment_result.get("label")

        # Step 3 - Normalize fields
        summary, sentiment_label = normalize_content_fields(summary, sentiment_label)

        # Step 4 - Save to database
        db_content = Content(
            title=title,
            source=source,
            summary=summary,
            sentiment=sentiment_label
        )

        db.add(db_content)
        db.commit()
        db.refresh(db_content)

        return {
            "id": db_content.id,
            "title": title,
            "summary": summary,
            "sentiment": sentiment_label
        }
