import os
import re
import logging
from typing import List
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self, model_name: str = None):
        self.model_name = model_name or os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        logger.info("Initializing EmbeddingService with model: %s", self.model_name)
        self.model = SentenceTransformer(self.model_name)

    @staticmethod
    def clean_text(text: str) -> str:
        if not text:
            return ""
        # Remove extra whitespaces and control characters
        cleaned = re.sub(r"\s+", " ", text).strip()
        return cleaned

    def chunk_text(self, text: str, chunk_size: int = 300, chunk_overlap: int = 50) -> List[str]:
        """
        Split text into word-based chunks if text exceeds chunk_size words.
        """
        cleaned = self.clean_text(text)
        if not cleaned:
            return []

        words = cleaned.split(" ")
        if len(words) <= chunk_size:
            return [cleaned]

        chunks = []
        step = chunk_size - chunk_overlap
        if step <= 0:
            step = chunk_size

        for i in range(0, len(words), step):
            chunk = " ".join(words[i : i + chunk_size])
            if chunk:
                chunks.append(chunk)

        return chunks

    def generate_embedding(self, text: str) -> List[float]:
        cleaned = self.clean_text(text)
        if not cleaned:
            return []
        embedding = self.model.encode(cleaned, convert_to_numpy=True)
        return embedding.tolist()

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        cleaned_texts = [self.clean_text(t) for t in texts]
        non_empty = [t if t else " " for t in cleaned_texts]
        embeddings = self.model.encode(non_empty, convert_to_numpy=True)
        return embeddings.tolist()

