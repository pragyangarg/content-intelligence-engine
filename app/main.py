from fastapi import FastAPI

from app.models.database import engine
from app.models import content
from app.api.routes import router

from app.services.summarizer import SummarizerService
from app.services.sentiment import SentimentService
from app.services.workflow import WorkflowEngine
from app.services.rss_monitor import RSSMonitor


app = FastAPI(
    title="Content Intelligence Engine",
    description="AI-powered content processing pipeline",
    version="1.0.0"
)

# Create database tables
content.Base.metadata.create_all(bind=engine)

# Register API routes
app.include_router(router)


# Global model references (initially empty)
summarizer_service = None
sentiment_service = None
rss_monitor = None
workflow_engine = None


@app.on_event("startup")
def load_models():
    
    global summarizer_service, sentiment_service, workflow_engine, rss_monitor

    print("Loading AI models...")

    summarizer_service = SummarizerService()
    sentiment_service = SentimentService()


    workflow_engine = WorkflowEngine(
        summarizer_service,
        sentiment_service
    )

    rss_monitor = RSSMonitor(workflow_engine)
    print("Models loaded successfully.")



from fastapi import Depends
from sqlalchemy.orm import Session
from app.models.database import SessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/process-content")
def process_content_endpoint(
    title: str,
    source: str,
    text: str,
    db: Session = Depends(get_db)
):
    return workflow_engine.process_content(title, source, text, db)

@app.post("/process-rss")
def process_rss_feed(
    rss_url: str,
    db: Session = Depends(get_db)
):
    return rss_monitor.fetch_and_process(rss_url, db)

@app.get("/")
def root():
    return {"message": "Content Intelligence Engine is running"}


@app.get("/test-summary")
def test_summary():
    text = """
    Artificial Intelligence is transforming industries worldwide.
    Companies are leveraging machine learning to automate processes,
    improve decision-making, and enhance customer experiences.
    """
    summary = summarizer_service.summarize(text)
    return {"summary": summary}


@app.get("/test-sentiment")
def test_sentiment():
    text = "Artificial Intelligence is absolutely amazing and revolutionary."
    result = sentiment_service.analyze(text)
    return result


