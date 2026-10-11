import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.content import Content, Base
from app.services.workflow import WorkflowEngine
from app.services.summarizer import SummarizerService
from app.services.sentiment import SentimentService


@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine)
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


def test_new_article_is_inserted(in_memory_db):
    summarizer = SummarizerService()
    sentiment = SentimentService()
    workflow = WorkflowEngine(summarizer, sentiment)

    result = workflow.process_content(
        title="Unique Tech News 2026",
        source="Test Source",
        text="A new technological breakthrough was announced today.",
        db=in_memory_db,
        url="https://example.com/unique-1",
    )

    assert "id" in result
    assert result["title"] == "Unique Tech News 2026"
    assert result.get("content_hash") is not None

    # Check persistence
    stored = in_memory_db.query(Content).filter(Content.title == "Unique Tech News 2026").first()
    assert stored is not None
    assert stored.source == "Test Source"
    assert stored.url == "https://example.com/unique-1"


def test_duplicate_article_is_ignored(in_memory_db):
    summarizer = SummarizerService()
    sentiment = SentimentService()
    workflow = WorkflowEngine(summarizer, sentiment)

    # First insert
    res1 = workflow.process_content(
        title="Duplicate Check Title",
        source="Test Source",
        text="Content for duplicate detection test.",
        db=in_memory_db,
        url="https://example.com/dup-1",
    )
    assert "id" in res1

    # Second insert with same title and URL
    res2 = workflow.process_content(
        title="Duplicate Check Title",
        source="Test Source",
        text="Content for duplicate detection test.",
        db=in_memory_db,
        url="https://example.com/dup-1",
    )
    assert res2.get("message") == "Article already processed"
    assert res2.get("id") == res1["id"]

    # Count total rows
    total_articles = in_memory_db.query(Content).count()
    assert total_articles == 1

