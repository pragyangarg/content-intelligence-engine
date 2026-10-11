import logging
from typing import List, Dict, Any
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)


class WebSearchService:
    def __init__(self, max_results: int = 3):
        self.max_results = max_results

    def search(self, query: str, max_results: int = None) -> List[Dict[str, Any]]:
        """
        Perform a web search fallback using DuckDuckGo.
        Returns a list of documents formatted identically to retrieved local articles.
        """
        k = max_results or self.max_results
        results: List[Dict[str, Any]] = []

        try:
            with DDGS() as ddgs:
                raw_results = list(ddgs.text(query, max_results=k))
                for i, r in enumerate(raw_results):
                    results.append({
                        "id": f"web_{i}",
                        "article_id": None,
                        "title": r.get("title", "Web Result"),
                        "source": "Web Search (DuckDuckGo)",
                        "url": r.get("href") or r.get("link") or "",
                        "published_at": "",
                        "content": r.get("body", ""),
                        "distance": 0.5,
                        "similarity": 0.5,
                    })
            logger.info("Web search retrieved %d results for query '%s'", len(results), query)
        except Exception as exc:
            logger.warning("Web search fallback failed or was rate-limited: %s", exc)

        return results


# Module-level reusable helper
def web_search(query: str, max_results: int = 3) -> List[Dict[str, Any]]:
    service = WebSearchService(max_results=max_results)
    return service.search(query)

