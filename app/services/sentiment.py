from transformers import pipeline


class SentimentService:
    def __init__(self):
        # Load classification model
        self.classifier = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english"
        )

    def analyze(self, text: str) -> dict:
        if not text.strip():
            return {"label": "UNKNOWN", "score": 0.0}

        result = self.classifier(text)

        return {
            "label": result[0]["label"],
            "score": float(result[0]["score"])
        }