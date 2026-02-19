from sqlalchemy.orm import Session
from app.models.content import Content


class WorkflowEngine:
    def __init__(self, summarizer_service, sentiment_service):
        self.summarizer = summarizer_service
        self.sentiment = sentiment_service

    def process_content(self, title: str, source: str, text: str, db: Session):
        # Step 1: Generate summary
        summary = self.summarizer.summarize(text)

        # Step 2: Analyze sentiment
        sentiment_result = self.sentiment.analyze(summary)

        # Step 3: Save to database
        db_content = Content(
            title=title,
            source=source,
            summary=summary,
            sentiment=sentiment_result["label"]
        )

        db.add(db_content)
        db.commit()
        db.refresh(db_content)

        return {
            "id": db_content.id,
            "title": title,
            "summary": summary,
            "sentiment": sentiment_result
        }