from transformers import pipeline

class SummarizerService:
    def __init__(self):
        # Load model only once during startup
        self.summarizer = pipeline(
            "summarization",
            model="facebook/bart-large-cnn",
            framework="pt"
        )
    def summarize(self, text: str) -> str:
        if len(text.strip()) == 0:
            return ""

        result = self.summarizer(
            text,
            max_length=60,
            min_length=10,
            do_sample=False
        )

        return result[0]["summary_text"]