import logging
import os

from transformers import pipeline


logger = logging.getLogger(__name__)

class SummarizerService:
    def __init__(self):
        self.summarizer = None

        if os.getenv("ENABLE_TRANSFORMER_MODELS", "").lower() != "true":
            logger.info("Transformer summarizer disabled; using fallback summarization.")
            return

        try:
            # Load model only once during startup
            self.summarizer = pipeline(
                "summarization",
                model="facebook/bart-large-cnn",
                framework="pt",
                local_files_only=True
            )
        except Exception as exc:
            logger.warning(
                "Falling back to extractive summarization because the model could not be loaded: %s",
                exc
            )

    def summarize(self, text: str) -> str:
        clean_text = text.strip()
        if len(clean_text) == 0:
            return ""

        if self.summarizer is None:
            return self._fallback_summary(clean_text)

        result = self.summarizer(
            clean_text,
            max_length=60,
            min_length=10,
            do_sample=False
        )

        return result[0]["summary_text"]

    def _fallback_summary(self, text: str) -> str:
        sentences = [part.strip() for part in text.replace("\n", " ").split(".") if part.strip()]
        if not sentences:
            return text[:240].strip()

        summary = ". ".join(sentences[:2]).strip()
        if summary and not summary.endswith("."):
            summary += "."

        return summary[:240]
