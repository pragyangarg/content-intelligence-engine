import os
import re
import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.model_name = os.getenv("LLM_MODEL", "gpt-4o-mini")
        self._openai_client = None

        if self.openai_api_key:
            try:
                from openai import OpenAI
                self._openai_client = OpenAI(api_key=self.openai_api_key)
                logger.info("LLMService initialized with OpenAI model: %s", self.model_name)
            except Exception as exc:
                logger.warning("Could not initialize OpenAI client: %s", exc)

    def analyze_query(self, query: str) -> str:
        """
        Extract core keywords and clean search intent from the query.
        """
        clean = query.strip()
        # Remove common conversational noise prefixes
        noise_patterns = [
            r"^(please\s+)?(tell\s+me|show\s+me|find|search|give\s+me|what\s+is|what\s+are|who\s+is|explain|can\s+you\s+tell\s+me\s+about)\s+",
            r"\?+$",
        ]
        rewritten = clean
        for pattern in noise_patterns:
            rewritten = re.sub(pattern, "", rewritten, flags=re.IGNORECASE).strip()

        # If LLM is available, could also refine, but deterministic rule-based is fast and robust
        return rewritten if len(rewritten) > 3 else clean

    def generate_answer(
        self,
        query: str,
        documents: List[Dict[str, Any]]
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Generate grounded answer with citations using provided context documents.
        Returns: (answer_string, citations_list)
        """
        # Deduplicate and extract citations
        citations = []
        seen_titles = set()
        for doc in documents:
            title = doc.get("title", "Untitled")
            if title and title not in seen_titles:
                seen_titles.add(title)
                citations.append({
                    "title": title,
                    "url": doc.get("url", ""),
                    "source": doc.get("source", ""),
                })

        if not documents:
            answer = "I could not find enough relevant information in the knowledge base or web search to answer your query."
            return answer, []

        context_blocks = []
        for i, doc in enumerate(documents, 1):
            title = doc.get("title", f"Document {i}")
            source = doc.get("source", "Unknown")
            content = doc.get("content", "").strip()
            context_blocks.append(f"[{i}] {title} (Source: {source})\n{content}")

        context_text = "\n\n".join(context_blocks)

        system_prompt = (
            "You are a helpful and accurate Content Intelligence Assistant. "
            "Answer the user query based ONLY on the provided context. "
            "Do not invent facts or extrapolate beyond what is given. "
            "If the context does not contain sufficient information, state that clearly. "
            "Always cite the source numbers or titles when referencing facts."
        )

        user_prompt = (
            f"Context:\n{context_text}\n\n"
            f"User Question: {query}\n\n"
            "Provide a concise, direct answer based strictly on the context above."
        )

        # 1. Attempt OpenAI generation if client is configured
        if self._openai_client:
            try:
                response = self._openai_client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.2,
                    max_tokens=500,
                )
                generated = response.choices[0].message.content.strip()
                answer = self._append_citations(generated, citations)
                return answer, citations
            except Exception as exc:
                logger.warning("OpenAI generation failed, falling back to local synthesis: %s", exc)

        # 2. Local deterministic grounded synthesis fallback
        answer = self._local_grounded_answer(query, documents, citations)
        return answer, citations

    def _local_grounded_answer(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        citations: List[Dict[str, Any]]
    ) -> str:
        """
        Deterministic local answer synthesis extracting most relevant sentences from documents.
        """
        query_words = set(re.findall(r"\w+", query.lower())) - {"what", "is", "are", "the", "in", "on", "a", "an", "and", "or", "of", "to", "for"}

        relevant_sentences = []
        for doc in documents:
            content = doc.get("content", "")
            title = doc.get("title", "")
            # Split into sentences
            sentences = [s.strip() for s in re.split(r"[.\n]+", content) if len(s.strip()) > 20]
            for s in sentences:
                s_words = set(re.findall(r"\w+", s.lower()))
                overlap = len(query_words.intersection(s_words))
                if overlap > 0:
                    relevant_sentences.append((overlap, title, s))

        relevant_sentences.sort(key=lambda x: x[0], reverse=True)
        top_sentences = relevant_sentences[:3]

        if top_sentences:
            synthesis_parts = []
            for _, title, s in top_sentences:
                clean_s = s if s.endswith(".") else f"{s}."
                synthesis_parts.append(f"According to {title}, {clean_s}")
            body = " ".join(synthesis_parts)
        else:
            first_doc = documents[0]
            summary_snippet = first_doc.get("content", "")[:280].strip()
            if not summary_snippet.endswith("."):
                summary_snippet += "..."
            body = f"Based on {first_doc.get('title', 'retrieved articles')}: {summary_snippet}"

        return self._append_citations(body, citations)

    def _append_citations(self, text: str, citations: List[Dict[str, Any]]) -> str:
        if not citations:
            return text

        lines = [text.strip(), "", "Sources:"]
        for i, c in enumerate(citations, 1):
            title = c.get("title", "Untitled")
            source = c.get("source", "")
            url = c.get("url", "")
            ref = f"{i}. {title}"
            if source:
                ref += f" - {source}"
            if url:
                ref += f" ({url})"
            lines.append(ref)

        return "\n".join(lines)


# Singleton instance
_default_llm_service = None


def get_llm_service() -> LLMService:
    global _default_llm_service
    if _default_llm_service is None:
        _default_llm_service = LLMService()
    return _default_llm_service

