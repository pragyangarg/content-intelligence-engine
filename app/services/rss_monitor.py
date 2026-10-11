import time
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
import feedparser

logger = logging.getLogger(__name__)

POPULAR_FEEDS: Dict[str, str] = {
    "TechCrunch": "https://techcrunch.com/feed/",
    "The Verge": "https://www.theverge.com/rss/index.xml",
    "Wired": "https://www.wired.com/feed/rss",
    "Ars Technica": "https://feeds.arstechnica.com/arstechnica/index",
    "BBC Technology": "https://feeds.bbci.co.uk/news/technology/rss.xml",
    "MIT Technology Review": "https://www.technologyreview.com/feed/",
    "Engadget": "https://www.engadget.com/rss.xml",
    "Hacker News": "https://news.ycombinator.com/rss",
}


class RSSMonitor:
    def __init__(self, workflow_engine):
        self.workflow = workflow_engine

    def _parse_published_date(self, entry) -> Optional[datetime]:
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                return datetime.fromtimestamp(time.mktime(entry.published_parsed))
            except Exception:
                pass
        return None

    def fetch_and_process(self, rss_url: str, db, limit: int = 10) -> List[Dict[str, Any]]:
        feed = feedparser.parse(rss_url)
        results = []

        for entry in feed.entries[:limit]:
            title = getattr(entry, "title", "Untitled")
            source = getattr(feed.feed, "title", rss_url) or rss_url
            url = getattr(entry, "link", None)
            published_at = self._parse_published_date(entry)

            # Extract best available content
            text = ""
            if hasattr(entry, "content") and entry.content:
                text = entry.content[0].get("value", "")
            if not text and hasattr(entry, "summary"):
                text = entry.summary
            if not text and hasattr(entry, "description"):
                text = entry.description

            result = self.workflow.process_content(
                title=title,
                source=source,
                text=text or title,
                db=db,
                url=url,
                published_at=published_at,
            )
            results.append(result)

        logger.info("Processed %d entries from feed '%s'", len(results), rss_url)
        return results

    def fetch_multiple_feeds(self, rss_urls: List[str], db, limit_per_feed: int = 10) -> List[Dict[str, Any]]:
        all_results = []
        for url in rss_urls:
            try:
                res = self.fetch_and_process(url, db, limit=limit_per_feed)
                all_results.extend(res)
            except Exception as exc:
                logger.warning("Failed to fetch RSS feed %s: %s", url, exc)
        return all_results