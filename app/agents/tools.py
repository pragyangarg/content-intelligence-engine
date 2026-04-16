from langchain_core.tools import tool

from app.services.summarizer import SummarizerService
from app.services.sentiment import SentimentService


# Initialize services
summarizer = SummarizerService()
sentiment = SentimentService()


@tool
def summarize_tool(text: str) -> str:
    """
    Summarize an article using a transformer model.
    """
    return summarizer.summarize(text)


@tool
def sentiment_tool(text: str) -> str:
    """
    Analyze sentiment of a text using transformer model.
    """
    result = sentiment.analyze(text)
    return result["label"]