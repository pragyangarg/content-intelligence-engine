import os
import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings

from app.services.embedding_service import EmbeddingService
from app.models.content import Content

logger = logging.getLogger(__name__)


class VectorStoreService:
    def __init__(
        self,
        embedding_service: Optional[EmbeddingService] = None,
        persist_directory: Optional[str] = None,
        collection_name: Optional[str] = None
    ):
        self.embedding_service = embedding_service or EmbeddingService()
        self.persist_dir = persist_directory or os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
        self.collection_name = collection_name or os.getenv("CHROMA_COLLECTION_NAME", "articles")

        logger.info(
            "Initializing ChromaDB client at '%s' with collection '%s'",
            self.persist_dir,
            self.collection_name
        )
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def index_content(self, content_item: Any) -> int:
        """
        Index an article into ChromaDB.
        Accepts a Content model instance or dictionary.
        """
        article_id = getattr(content_item, "id", None) or content_item.get("id")
        title = getattr(content_item, "title", "") or content_item.get("title", "")
        body = (
            getattr(content_item, "content", None)
            or getattr(content_item, "summary", "")
            or content_item.get("content")
            or content_item.get("summary", "")
            or ""
        )
        source = getattr(content_item, "source", "") or content_item.get("source", "")
        url = getattr(content_item, "url", "") or content_item.get("url", "")
        published_at = str(getattr(content_item, "published_at", "") or content_item.get("published_at", ""))

        # Combine title and body for better semantic context
        full_text = f"{title}\n\n{body}".strip() if title else body.strip()
        if not full_text:
            return 0

        chunks = self.embedding_service.chunk_text(full_text)
        if not chunks:
            return 0

        embeddings = self.embedding_service.generate_embeddings(chunks)

        try:
            art_id_val = int(article_id)
        except (ValueError, TypeError):
            art_id_val = -1

        ids = [f"article_{article_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "article_id": art_id_val,
                "title": title or "",
                "source": source or "",
                "url": url or "",
                "published_at": published_at or "",
                "chunk_index": i,
            }
            for i in range(len(chunks))
        ]

        # Upsert into ChromaDB
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas
        )

        logger.info("Indexed %d chunk(s) for article id %s", len(chunks), article_id)
        return len(chunks)

    def search_documents(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Semantic search for top_k documents given a query string.
        """
        clean_query = self.embedding_service.clean_text(query)
        if not clean_query:
            return []

        # If collection is empty, return empty list
        if self.collection.count() == 0:
            return []

        query_embedding = self.embedding_service.generate_embedding(clean_query)
        if not query_embedding:
            return []

        actual_k = min(top_k, self.collection.count())
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=actual_k,
            include=["documents", "metadatas", "distances"]
        )

        documents = []
        if results and results.get("ids") and len(results["ids"]) > 0:
            ids = results["ids"][0]
            docs = results["documents"][0] if results.get("documents") else []
            metas = results["metadatas"][0] if results.get("metadatas") else []
            distances = results["distances"][0] if results.get("distances") else []

            for i in range(len(ids)):
                meta = metas[i] if i < len(metas) else {}
                distance = float(distances[i]) if i < len(distances) else 1.0
                # Cosine distance to similarity: similarity = 1 - distance
                similarity = max(0.0, min(1.0, 1.0 - distance))

                documents.append({
                    "id": ids[i],
                    "article_id": meta.get("article_id"),
                    "title": meta.get("title", ""),
                    "source": meta.get("source", ""),
                    "url": meta.get("url", ""),
                    "published_at": meta.get("published_at", ""),
                    "content": docs[i] if i < len(docs) else "",
                    "distance": distance,
                    "similarity": similarity
                })

        return documents

    def backfill_from_db(self, db_session) -> int:
        """
        Backfill all articles from SQLite into ChromaDB if not already indexed.
        """
        contents = db_session.query(Content).all()
        indexed_count = 0
        for item in contents:
            chunks_indexed = self.index_content(item)
            if chunks_indexed > 0:
                indexed_count += 1
        return indexed_count


# Global singleton and module-level helper for reuse across services
_default_vector_store: Optional[VectorStoreService] = None


def get_vector_store() -> VectorStoreService:
    global _default_vector_store
    if _default_vector_store is None:
        _default_vector_store = VectorStoreService()
    return _default_vector_store


def search_documents(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Reusable standalone retrieval function."""
    return get_vector_store().search_documents(query=query, top_k=top_k)

