import ast
import json
from typing import Optional, Tuple


def normalize_content_fields(
    summary: Optional[str],
    sentiment: Optional[str]
) -> Tuple[Optional[str], Optional[str]]:
    if not isinstance(summary, str):
        return summary, sentiment

    raw_summary = summary.strip()
    if not raw_summary:
        return summary, sentiment

    parsed_payload = None

    for parser in (json.loads, ast.literal_eval):
        try:
            candidate = parser(raw_summary)
        except (ValueError, SyntaxError, TypeError, json.JSONDecodeError):
            continue

        if isinstance(candidate, dict):
            parsed_payload = candidate
            break

    if not parsed_payload:
        return summary, sentiment

    clean_summary = parsed_payload.get("summary", summary)
    clean_sentiment = parsed_payload.get("sentiment", sentiment)

    if not isinstance(clean_summary, str):
        clean_summary = str(clean_summary)

    if clean_sentiment is not None and not isinstance(clean_sentiment, str):
        clean_sentiment = str(clean_sentiment)

    return clean_summary, clean_sentiment
