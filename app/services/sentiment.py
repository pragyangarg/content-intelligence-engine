import logging
import os

from transformers import pipeline


logger = logging.getLogger(__name__)


class SentimentService:
    def __init__(self):
        self.classifier = None

        if os.getenv("ENABLE_TRANSFORMER_MODELS", "").lower() != "true":
            logger.info("Transformer sentiment model disabled; using fallback sentiment.")
            return

        try:
            # Load classification model
            self.classifier = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english",
                local_files_only=True
            )
        except Exception as exc:
            logger.warning(
                "Falling back to rule-based sentiment because the model could not be loaded: %s",
                exc
            )

    def analyze(self, text: str) -> dict:
        if not text.strip():
            return {"label": "UNKNOWN", "score": 0.0}

        if self.classifier is None:
            return self._fallback_analyze(text)

        result = self.classifier(text)

        return {
            "label": result[0]["label"],
            "score": float(result[0]["score"])
        }

    def _fallback_analyze(self, text: str) -> dict:
        lowered = text.lower()
        positive_words = {"good", "great", "excellent", "amazing", "positive", "success", "happy"}
        negative_words = {"bad", "poor", "terrible", "awful", "negative", "fail", "sad"}

        positive_hits = sum(word in lowered for word in positive_words)
        negative_hits = sum(word in lowered for word in negative_words)

        if positive_hits > negative_hits:
            return {"label": "POSITIVE", "score": 0.6}
        if negative_hits > positive_hits:
            return {"label": "NEGATIVE", "score": 0.6}
        return {"label": "NEUTRAL", "score": 0.5}
