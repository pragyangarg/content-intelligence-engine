import logging
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, START, END

from app.services.vector_store import get_vector_store, VectorStoreService
from app.services.llm_service import get_llm_service, LLMService
from app.services.web_search import WebSearchService

logger = logging.getLogger(__name__)


class RAGState(TypedDict):
    query: str
    rewritten_query: str
    documents: List[Dict[str, Any]]
    needs_web_search: bool
    web_documents: List[Dict[str, Any]]
    answer: str
    citations: List[Dict[str, Any]]


class AgenticRAGWorkflow:
    def __init__(
        self,
        vector_store: Optional[VectorStoreService] = None,
        llm_service: Optional[LLMService] = None,
        web_search_service: Optional[WebSearchService] = None,
        similarity_threshold: float = 0.25,
    ):
        self.vector_store = vector_store or get_vector_store()
        self.llm_service = llm_service or get_llm_service()
        self.web_search_service = web_search_service or WebSearchService()
        self.similarity_threshold = similarity_threshold
        self.graph = self._build_graph()

    # --- Node 1: Query Analysis ---
    def analyze_query_node(self, state: RAGState) -> Dict[str, Any]:
        query = state.get("query", "")
        rewritten = self.llm_service.analyze_query(query)
        logger.info("Query analysis: '%s' -> '%s'", query, rewritten)
        return {"rewritten_query": rewritten}

    # --- Node 2: Vector Search ---
    def vector_search_node(self, state: RAGState) -> Dict[str, Any]:
        search_query = state.get("rewritten_query") or state.get("query", "")
        docs = self.vector_store.search_documents(search_query, top_k=5)
        logger.info("Vector search returned %d document(s)", len(docs))
        return {"documents": docs}

    # --- Node 3: Filter / Rerank ---
    def filter_rerank_node(self, state: RAGState) -> Dict[str, Any]:
        raw_docs = state.get("documents", [])
        # Filter documents by similarity score
        filtered_docs = [
            d for d in raw_docs
            if d.get("similarity", 0.0) >= self.similarity_threshold
        ]

        # Sort remaining docs by similarity descending
        filtered_docs.sort(key=lambda d: d.get("similarity", 0.0), reverse=True)
        # Keep top 3 most relevant
        kept_docs = filtered_docs[:3]

        # Check if local context is sufficient
        needs_web = len(kept_docs) == 0
        logger.info(
            "Filtering kept %d of %d documents. Needs web fallback: %s",
            len(kept_docs),
            len(raw_docs),
            needs_web
        )
        return {
            "documents": kept_docs,
            "needs_web_search": needs_web
        }

    # --- Conditional Router ---
    def route_after_filter(self, state: RAGState) -> str:
        if state.get("needs_web_search", False):
            return "web_search"
        return "generate_answer"

    # --- Node 4: Web Search Fallback ---
    def web_search_node(self, state: RAGState) -> Dict[str, Any]:
        query = state.get("rewritten_query") or state.get("query", "")
        logger.info("Running web search fallback for: %s", query)
        web_docs = self.web_search_service.search(query, max_results=3)
        combined_docs = state.get("documents", []) + web_docs
        return {
            "web_documents": web_docs,
            "documents": combined_docs
        }

    # --- Node 5: Generate Answer ---
    def generate_answer_node(self, state: RAGState) -> Dict[str, Any]:
        query = state.get("query", "")
        docs = state.get("documents", [])
        answer, citations = self.llm_service.generate_answer(query, docs)
        return {
            "answer": answer,
            "citations": citations
        }

    def _build_graph(self):
        builder = StateGraph(RAGState)

        # Add Nodes
        builder.add_node("analyze_query", self.analyze_query_node)
        builder.add_node("vector_search", self.vector_search_node)
        builder.add_node("filter_rerank", self.filter_rerank_node)
        builder.add_node("web_search", self.web_search_node)
        builder.add_node("generate_answer", self.generate_answer_node)

        # Add Edges
        builder.add_edge(START, "analyze_query")
        builder.add_edge("analyze_query", "vector_search")  
        builder.add_edge("vector_search", "filter_rerank")

        builder.add_conditional_edges(
            "filter_rerank",
            self.route_after_filter,
            {
                "web_search": "web_search",
                "generate_answer": "generate_answer",
            }
        )

        builder.add_edge("web_search", "generate_answer")
        builder.add_edge("generate_answer", END)

        return builder.compile()

    def run(self, query: str) -> Dict[str, Any]:
        initial_state: RAGState = {
            "query": query,
            "rewritten_query": "",
            "documents": [],
            "needs_web_search": False,
            "web_documents": [],
            "answer": "",
            "citations": [],
        }
        final_state = self.graph.invoke(initial_state)
        return final_state

    def run_baseline(self, query: str) -> Dict[str, Any]:
        """
        Version A (Baseline RAG):
        Raw Query -> Vector Search -> LLM Generation (no query analysis, no filtering, no web fallback)
        """
        raw_docs = self.vector_store.search_documents(query, top_k=5)
        answer, citations = self.llm_service.generate_answer(query, raw_docs)
        return {
            "query": query,
            "rewritten_query": query,
            "documents": raw_docs,
            "needs_web_search": False,
            "web_documents": [],
            "answer": answer,
            "citations": citations,
        }


# Global workflow instance
_default_rag_workflow: Optional[AgenticRAGWorkflow] = None


def get_rag_workflow() -> AgenticRAGWorkflow:
    global _default_rag_workflow
    if _default_rag_workflow is None:
        _default_rag_workflow = AgenticRAGWorkflow()
    return _default_rag_workflow


def ask_engine(query: str) -> Dict[str, Any]:
    """Execute the full agentic RAG workflow for a user query."""
    workflow = get_rag_workflow()
    return workflow.run(query)

